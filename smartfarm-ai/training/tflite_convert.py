"""
SmartFarm AI - TFLite Conversion & Inference Example
Converts trained Keras model → quantized TFLite and demonstrates mobile inference.
"""

import os
import sys
import json
import argparse
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

MODEL_DIR = os.path.join(PROJECT_ROOT, "model")
H5_PATH = os.path.join(MODEL_DIR, "smartfarm_model.h5")
TFLITE_PATH = os.path.join(MODEL_DIR, "smartfarm_model.tflite")
CLASS_NAMES_PATH = os.path.join(MODEL_DIR, "class_names.json")


# ---------------------------------------------------------------------------
# Conversion
# ---------------------------------------------------------------------------
def convert_model(h5_path: str = H5_PATH, tflite_path: str = TFLITE_PATH):
    """Convert a Keras .h5 model to a quantized TFLite flat-buffer."""
    import tensorflow as tf

    print(f"[INFO] Loading Keras model from {h5_path} ...")
    model = tf.keras.models.load_model(h5_path)

    converter = tf.lite.TFLiteConverter.from_keras_model(model)

    # Post-training float16 quantization → ~50% smaller model
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_types = [tf.float16]

    print("[INFO] Converting ...")
    tflite_model = converter.convert()

    os.makedirs(os.path.dirname(tflite_path), exist_ok=True)
    with open(tflite_path, "wb") as f:
        f.write(tflite_model)

    size_mb = os.path.getsize(tflite_path) / (1024 * 1024)
    print(f"[INFO] Saved TFLite model → {tflite_path}  ({size_mb:.1f} MB)")


# ---------------------------------------------------------------------------
# TFLite inference (simulates mobile usage)
# ---------------------------------------------------------------------------
class TFLitePredictor:
    """Lightweight predictor using the TFLite runtime — no full TensorFlow needed."""

    def __init__(self, tflite_path: str = TFLITE_PATH, class_names_path: str = CLASS_NAMES_PATH):
        import tflite_runtime.interpreter as tflite  # noqa: F811
        self._use_tflite_runtime = True
        self._init_interpreter(tflite, tflite_path, class_names_path)

    def _init_interpreter(self, tflite_module, tflite_path, class_names_path):
        self.interpreter = tflite_module.Interpreter(model_path=tflite_path)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        with open(class_names_path) as f:
            self.class_names = json.load(f)

        print(f"[INFO] TFLite model loaded: {tflite_path}")
        print(f"[INFO] Input shape : {self.input_details[0]['shape']}")
        print(f"[INFO] Output shape: {self.output_details[0]['shape']}")

    def predict(self, image_array: np.ndarray) -> dict:
        """Run inference on a preprocessed image array (1, 224, 224, 3) float32."""
        input_data = image_array.astype(np.float32)
        self.interpreter.set_tensor(self.input_details[0]["index"], input_data)
        self.interpreter.invoke()
        output = self.interpreter.get_tensor(self.output_details[0]["index"])[0]

        predicted_idx = int(np.argmax(output))
        confidence = float(output[predicted_idx])
        return {
            "disease": self.class_names[predicted_idx],
            "confidence": round(confidence, 4),
            "all_scores": {self.class_names[i]: round(float(output[i]), 4) for i in range(len(output))},
        }


class TFLitePredictorFull:
    """Fallback predictor using full TensorFlow (when tflite_runtime is not installed)."""

    def __init__(self, tflite_path: str = TFLITE_PATH, class_names_path: str = CLASS_NAMES_PATH):
        import tensorflow as tf

        self.interpreter = tf.lite.Interpreter(model_path=tflite_path)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        with open(class_names_path) as f:
            self.class_names = json.load(f)

        print(f"[INFO] TFLite model loaded (via full TF): {tflite_path}")

    def predict(self, image_array: np.ndarray) -> dict:
        input_data = image_array.astype(np.float32)
        self.interpreter.set_tensor(self.input_details[0]["index"], input_data)
        self.interpreter.invoke()
        output = self.interpreter.get_tensor(self.output_details[0]["index"])[0]

        predicted_idx = int(np.argmax(output))
        confidence = float(output[predicted_idx])
        return {
            "disease": self.class_names[predicted_idx],
            "confidence": round(confidence, 4),
        }


def get_predictor(tflite_path: str = TFLITE_PATH, class_names_path: str = CLASS_NAMES_PATH):
    """Return the best available TFLite predictor."""
    try:
        return TFLitePredictor(tflite_path, class_names_path)
    except ImportError:
        print("[WARN] tflite_runtime not found, falling back to full TensorFlow.")
        return TFLitePredictorFull(tflite_path, class_names_path)


# ---------------------------------------------------------------------------
# Demo inference
# ---------------------------------------------------------------------------
def demo_inference(image_path: str):
    """Run a demo prediction on a single image file."""
    from utils.preprocess import preprocess_image_from_path
    from utils.advice import get_advice

    print(f"\n[DEMO] Running TFLite inference on: {image_path}")
    predictor = get_predictor()

    img = preprocess_image_from_path(image_path)
    result = predictor.predict(img)

    advice_en = get_advice(result["disease"], "en")
    advice_hi = get_advice(result["disease"], "hi")

    print(f"\n  Disease    : {result['disease']}")
    print(f"  Confidence : {result['confidence'] * 100:.1f}%")
    print(f"  Advice (EN): {advice_en}")
    print(f"  Advice (HI): {advice_hi}")
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="SmartFarm AI - TFLite tools")
    sub = parser.add_subparsers(dest="command")

    # convert
    conv_parser = sub.add_parser("convert", help="Convert .h5 → .tflite")
    conv_parser.add_argument("--model", default=H5_PATH, help="Path to .h5 model")
    conv_parser.add_argument("--output", default=TFLITE_PATH, help="Output .tflite path")

    # predict
    pred_parser = sub.add_parser("predict", help="Run TFLite inference on an image")
    pred_parser.add_argument("image", help="Path to leaf image file")

    args = parser.parse_args()

    if args.command == "convert":
        convert_model(args.model, args.output)
    elif args.command == "predict":
        demo_inference(args.image)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
