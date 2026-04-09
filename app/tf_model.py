"""
SmartFarm AI - TensorFlow Model Integration
────────────────────────────────────────────
Provides a singleton TF/TFLite model loader for crop disease classification.
Uses two-stage validation via knowledge_engine.CROP_DISEASE_MAP.
"""

import os
import io
import json
import logging
import numpy as np
from PIL import Image

from app.knowledge_engine import (
    get_knowledge,
    validate_crop_disease,
    get_confidence_message,
    _parse_class,
    CROP_DISEASE_MAP,
)

logger = logging.getLogger(__name__)

# Paths
_PROJECT_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "smartfarm-ai")
_MODEL_DIR = os.path.join(_PROJECT_ROOT, "model")
_H5_PATH = os.path.join(_MODEL_DIR, "smartfarm_model.h5")
_TFLITE_PATH = os.path.join(_MODEL_DIR, "smartfarm_model.tflite")
_CLASS_NAMES_PATH = os.path.join(_MODEL_DIR, "class_names.json")

# Singleton
_model = None
_class_names = None
_model_type = None  # "tflite" | "keras" | None
_model_mtime = 0    # file mod time — reload when training saves new checkpoint

IMG_SIZE = (224, 224)  # Default for EfficientNetB0; will be overridden from model if possible
_actual_img_size = None  # Auto-detected from loaded model

# Classes to always skip
_SKIP_CLASSES = {"Background_without_leaves"}


def is_model_available() -> bool:
    """Check if a trained model exists."""
    return os.path.exists(_TFLITE_PATH) or os.path.exists(_H5_PATH)


def _load_model():
    """Lazy-load the best available model. Reloads if the file on disk is newer."""
    global _model, _class_names, _model_type, _model_mtime, _actual_img_size

    # Check if model file was updated (e.g. training saved a new checkpoint)
    current_mtime = 0
    for p in (_TFLITE_PATH, _H5_PATH):
        if os.path.exists(p):
            current_mtime = max(current_mtime, os.path.getmtime(p))
    if _model is not None and current_mtime > _model_mtime:
        logger.info("[SmartFarm TF] Model file updated on disk — reloading")
        _model = None

    if _model is not None:
        return

    # Load class names
    if os.path.exists(_CLASS_NAMES_PATH):
        with open(_CLASS_NAMES_PATH) as f:
            _class_names = json.load(f)
        logger.info(f"[SmartFarm TF] Loaded {len(_class_names)} class names")
    else:
        logger.warning(f"[SmartFarm TF] No class_names.json found at {_CLASS_NAMES_PATH}")
        return

    # Try TFLite first (faster, smaller footprint)
    if os.path.exists(_TFLITE_PATH):
        try:
            import tensorflow as tf
            interpreter = tf.lite.Interpreter(model_path=_TFLITE_PATH)
            interpreter.allocate_tensors()
            _model = interpreter
            _model_type = "tflite"
            _model_mtime = os.path.getmtime(_TFLITE_PATH)
            # Auto-detect input size from TFLite model
            input_shape = interpreter.get_input_details()[0]["shape"]
            _actual_img_size = (int(input_shape[1]), int(input_shape[2]))
            logger.info(f"[SmartFarm TF] Loaded TFLite model ({_actual_img_size[0]}x{_actual_img_size[1]})")
            return
        except Exception as e:
            logger.warning(f"[SmartFarm TF] TFLite load failed: {e}")

    # Fallback to full Keras model
    if os.path.exists(_H5_PATH):
        try:
            import tensorflow as tf
            _model = tf.keras.models.load_model(_H5_PATH)
            _model_type = "keras"
            _model_mtime = os.path.getmtime(_H5_PATH)
            # Auto-detect input size from Keras model
            input_shape = _model.input_shape
            if input_shape and len(input_shape) >= 3:
                _actual_img_size = (int(input_shape[1]), int(input_shape[2]))
            logger.info(f"[SmartFarm TF] Loaded Keras model ({_actual_img_size[0]}x{_actual_img_size[1]})")
            return
        except Exception as e:
            logger.warning(f"[SmartFarm TF] Keras model load failed: {e}")

    logger.warning("[SmartFarm TF] No model could be loaded")


def predict_from_base64(image_base64: str) -> dict | None:
    """Predict disease from a base64-encoded image.
    
    Returns dict with keys: class_name, confidence, crop, disease,
    knowledge, confidence_warning, top_candidates — or None.
    """
    import base64

    if not is_model_available():
        return None

    _load_model()
    if _model is None or _class_names is None:
        return None

    try:
        image_bytes = base64.b64decode(image_base64)
        return _predict_from_bytes(image_bytes)
    except Exception as e:
        logger.error(f"[SmartFarm TF] Prediction failed: {e}")
        return None


def predict_from_bytes(image_bytes: bytes) -> dict | None:
    """Predict disease from raw image bytes."""
    if not is_model_available():
        return None

    _load_model()
    if _model is None or _class_names is None:
        return None

    try:
        return _predict_from_bytes(image_bytes)
    except Exception as e:
        logger.error(f"[SmartFarm TF] Prediction failed: {e}")
        return None


def _predict_from_bytes(image_bytes: bytes) -> dict:
    """Internal prediction with two-stage validation and confidence intelligence."""
    # Use auto-detected size or fall back to default
    img_size = _actual_img_size or IMG_SIZE
    
    # Preprocess
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize(img_size, Image.LANCZOS)
    arr = np.array(img, dtype=np.float32) / 255.0
    input_data = np.expand_dims(arr, axis=0)

    # Run inference
    if _model_type == "tflite":
        input_details = _model.get_input_details()
        output_details = _model.get_output_details()
        _model.set_tensor(input_details[0]["index"], input_data)
        _model.invoke()
        output = _model.get_tensor(output_details[0]["index"])[0]
    else:
        output = _model.predict(input_data, verbose=0)[0]

    # Get top-10 predictions (enough to find valid crop-disease pairs)
    top_indices = np.argsort(output)[::-1][:10]

    # Build candidate list (skip Background and other invalid classes)
    candidates = []
    for idx in top_indices:
        cn = _class_names[idx]
        if cn in _SKIP_CLASSES:
            continue
        conf = float(output[idx])
        crop, disease = _parse_class(cn)
        candidates.append({
            "class_name": cn,
            "confidence": conf,
            "crop": crop,
            "disease": disease,
        })

    if not candidates:
        # Extreme edge case — return first non-background
        first = _class_names[top_indices[0]]
        crop, disease = _parse_class(first)
        candidates = [{"class_name": first, "confidence": float(output[top_indices[0]]),
                        "crop": crop, "disease": disease}]

    # ── Two-stage validation ──────────────────────────────────────────
    # Pick the best candidate where crop-disease relationship is valid.
    # If top-1 confidence is < 0.7, check top candidates for a better
    # valid crop–disease pair.
    best = candidates[0]
    if best["confidence"] < 0.7 and len(candidates) > 1:
        for cand in candidates:
            if validate_crop_disease(cand["crop"], cand["disease"]):
                best = cand
                break
    elif not validate_crop_disease(best["crop"], best["disease"]):
        # Top-1 is invalid pair — find first valid
        for cand in candidates[1:]:
            if validate_crop_disease(cand["crop"], cand["disease"]):
                best = cand
                break

    # ── Knowledge lookup ──────────────────────────────────────────────
    knowledge = get_knowledge(best["class_name"])

    # ── Confidence intelligence ───────────────────────────────────────
    confidence_warning = get_confidence_message(best["confidence"])

    # ── Top candidates for display (max 3, skip Background) ──────────
    top_display = []
    for c in candidates[:3]:
        label = f"{c['crop']} — {c['disease']}" if c["disease"] else f"{c['crop']} (Healthy)"
        top_display.append({
            "label": label,
            "confidence": round(c["confidence"] * 100, 1),
        })

    return {
        "class_name": best["class_name"],
        "confidence": best["confidence"],
        "crop": knowledge["crop"],
        "disease": knowledge["disease"],
        "knowledge": knowledge,
        "confidence_warning": confidence_warning,
        "top_candidates": top_display,
    }


def get_class_names() -> list:
    """Return the list of class names the model was trained on."""
    _load_model()
    return _class_names or []


def parse_class_name(class_name: str) -> tuple:
    """Parse a PlantVillage class name into (crop, disease_or_None)."""
    return _parse_class(class_name)
