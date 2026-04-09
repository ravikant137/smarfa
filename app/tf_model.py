"""
SmartFarm AI - TensorFlow Model Integration
Provides a singleton TF/TFLite model loader for crop disease classification.
Used by the main app's crop_ai.py for accurate predictions.
"""

import os
import io
import json
import logging
import numpy as np
from PIL import Image

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

IMG_SIZE = (160, 160)


def is_model_available() -> bool:
    """Check if a trained model exists."""
    return os.path.exists(_TFLITE_PATH) or os.path.exists(_H5_PATH)


def _load_model():
    """Lazy-load the best available model.  Reloads if the file on disk is newer."""
    global _model, _class_names, _model_type, _model_mtime

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
            logger.info(f"[SmartFarm TF] Loaded TFLite model from {_TFLITE_PATH}")
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
            logger.info(f"[SmartFarm TF] Loaded Keras model from {_H5_PATH}")
            return
        except Exception as e:
            logger.warning(f"[SmartFarm TF] Keras model load failed: {e}")

    logger.warning("[SmartFarm TF] No model could be loaded")


def predict_from_base64(image_base64: str) -> dict | None:
    """Predict disease from a base64-encoded image.
    
    Returns:
        dict with keys: class_name, confidence, top3 
        or None if model not available.
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
    """Internal prediction logic."""
    # Preprocess
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize(IMG_SIZE, Image.LANCZOS)
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

    # Get top-5 predictions (extra to skip non-crop classes)
    top_indices = np.argsort(output)[::-1][:5]
    
    top3 = []
    for idx in top_indices:
        top3.append({
            "class_name": _class_names[idx],
            "confidence": float(output[idx]),
        })

    predicted_idx = top_indices[0]
    predicted_class = _class_names[predicted_idx]

    # If the best prediction is "Background_without_leaves" (wide-field / non-leaf image),
    # use the next best real-crop prediction instead.
    if predicted_class == "Background_without_leaves":
        for idx in top_indices[1:]:
            if _class_names[idx] != "Background_without_leaves":
                predicted_idx = idx
                predicted_class = _class_names[idx]
                break

    return {
        "class_name": predicted_class,
        "confidence": float(output[predicted_idx]),
        "top3": [e for e in top3 if e["class_name"] != "Background_without_leaves"],
    }


def get_class_names() -> list:
    """Return the list of class names the model was trained on."""
    _load_model()
    return _class_names or []


def parse_class_name(class_name: str) -> tuple:
    """Parse a PlantVillage class name like 'Tomato___Early_blight' into (crop, disease).
    
    Returns (crop_name, disease_name_or_None).
    """
    if "___" in class_name:
        parts = class_name.split("___", 1)
        crop = parts[0].replace("_", " ").strip()
        disease_raw = parts[1].replace("_", " ").strip()
        
        # Clean up crop names
        crop = crop.replace("(maize)", "").replace(",  bell", "").strip()
        crop = crop.replace("Corn  maize", "Corn").replace("Pepper  bell", "Pepper")
        # Clean any extra parenthetical
        if "(" in crop:
            crop = crop.split("(")[0].strip()
        if "," in crop:
            crop = crop.split(",")[0].strip()
            
        if disease_raw.lower() == "healthy":
            return crop, None
        return crop, disease_raw
    
    return class_name, None
