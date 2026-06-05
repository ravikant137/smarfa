"""
SmartFarm AI - FastAPI Backend (Offline)
Serves crop disease predictions via REST API.
"""

import os
import sys
import json
from typing import Optional

import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from utils.preprocess import preprocess_image, IMG_SIZE
from utils.advice import get_advice, get_all_diseases, get_supported_languages

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
MODEL_DIR = os.path.join(PROJECT_ROOT, "model")
MODEL_PATH = os.path.join(MODEL_DIR, "smartfarm_model.h5")
TFLITE_PATH = os.path.join(MODEL_DIR, "smartfarm_model.tflite")
CLASS_NAMES_PATH = os.path.join(MODEL_DIR, "class_names.json")

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="SmartFarm AI",
    description="Offline crop disease detection and treatment advice API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Model loading (lazy singleton)
# ---------------------------------------------------------------------------
_model = None
_class_names = None


def _load_class_names() -> list:
    global _class_names
    if _class_names is None:
        with open(CLASS_NAMES_PATH) as f:
            _class_names = json.load(f)
    return _class_names


def _get_model():
    """Load the best available model (TFLite preferred, then full Keras)."""
    global _model

    if _model is not None:
        return _model

    # Try TFLite first (faster, smaller memory footprint)
    if os.path.exists(TFLITE_PATH):
        try:
            import tensorflow as tf

            interpreter = tf.lite.Interpreter(model_path=TFLITE_PATH)
            interpreter.allocate_tensors()
            _model = ("tflite", interpreter)
            print(f"[INFO] Loaded TFLite model from {TFLITE_PATH}")
            return _model
        except Exception as e:
            print(f"[WARN] TFLite load failed: {e}")

    # Fallback to full Keras model
    if os.path.exists(MODEL_PATH):
        import tensorflow as tf

        _model = ("keras", tf.keras.models.load_model(MODEL_PATH))
        print(f"[INFO] Loaded Keras model from {MODEL_PATH}")
        return _model

    raise RuntimeError("No model found. Train first with: python training/train.py")


def _predict(image_array: np.ndarray) -> tuple:
    """Run prediction and return (class_name, confidence)."""
    model_type, model = _get_model()
    class_names = _load_class_names()

    if model_type == "tflite":
        input_details = model.get_input_details()
        output_details = model.get_output_details()
        model.set_tensor(input_details[0]["index"], image_array.astype(np.float32))
        model.invoke()
        output = model.get_tensor(output_details[0]["index"])[0]
    else:
        output = model.predict(image_array, verbose=0)[0]

    predicted_idx = int(np.argmax(output))
    confidence = float(output[predicted_idx])
    return class_names[predicted_idx], confidence


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------
class PredictionResponse(BaseModel):
    disease: str
    confidence: float
    solution: str
    language_support: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    num_classes: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/", tags=["Info"])
async def root():
    return {"message": "SmartFarm AI API is running. POST an image to /predict"}


@app.get("/health", response_model=HealthResponse, tags=["Info"])
async def health():
    try:
        _get_model()
        class_names = _load_class_names()
        return HealthResponse(status="ok", model_loaded=True, num_classes=len(class_names))
    except Exception:
        return HealthResponse(status="no_model", model_loaded=False, num_classes=0)


@app.get("/diseases", tags=["Info"])
async def list_diseases():
    """Return all known diseases and supported languages."""
    return {
        "diseases": get_all_diseases(),
        "languages": get_supported_languages(),
    }


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict(
    file: UploadFile = File(..., description="Leaf image (JPEG/PNG)"),
    lang: str = Query("en", description="Language code for advice (en, hi, kn)"),
):
    """Upload a leaf image and get disease prediction + treatment advice."""
    # Validate content type
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image (JPEG/PNG).")

    # Read and limit file size (10 MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large. Max 10 MB.")

    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    try:
        image_array = preprocess_image(contents)
    except Exception:
        raise HTTPException(status_code=400, detail="Could not process image. Ensure it is a valid JPEG/PNG.")

    disease_name, confidence = _predict(image_array)
    solution = get_advice(disease_name, lang)

    return PredictionResponse(
        disease=disease_name,
        confidence=round(confidence, 4),
        solution=solution,
        language_support=lang,
    )


# ---------------------------------------------------------------------------
# Startup event
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup():
    """Pre-load model on server start for fast first prediction."""
    try:
        _get_model()
        _load_class_names()
        print("[INFO] Model pre-loaded successfully.")
    except Exception as e:
        print(f"[WARN] Model not available at startup: {e}")
        print("[WARN] Train a model first, then restart the server.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
