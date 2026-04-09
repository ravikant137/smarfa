"""
SmartFarm AI - Training Pipeline
Transfer learning with EfficientNetB0 + fine-tuning for crop disease detection.
Optimized for real-world farm images.
"""

import os
import sys
import json
import argparse
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, callbacks, mixed_precision
from sklearn.metrics import classification_report, confusion_matrix

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from utils.preprocess import create_data_generators, IMG_SIZE, BATCH_SIZE


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DEFAULT_DATASET_DIR = os.path.join(PROJECT_ROOT, "dataset")
MODEL_DIR = os.path.join(PROJECT_ROOT, "model")
MODEL_PATH = os.path.join(MODEL_DIR, "smartfarm_model.h5")
TFLITE_PATH = os.path.join(MODEL_DIR, "smartfarm_model.tflite")
CLASS_NAMES_PATH = os.path.join(MODEL_DIR, "class_names.json")

PHASE1_EPOCHS = 15
PHASE2_EPOCHS = 20
PHASE1_LR = 1e-3
PHASE2_LR = 1e-5
FINE_TUNE_AT = 100  # Unfreeze layers from this index onward in base model


# ---------------------------------------------------------------------------
# GPU / mixed precision setup
# ---------------------------------------------------------------------------
def setup_gpu():
    """Configure GPU memory growth and enable mixed precision if available."""
    gpus = tf.config.list_physical_devices("GPU")
    if gpus:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        print(f"[INFO] Found {len(gpus)} GPU(s). Enabling mixed precision.")
        mixed_precision.set_global_policy("mixed_float16")
    else:
        print("[INFO] No GPU found. Training on CPU.")


# ---------------------------------------------------------------------------
# Model builder
# ---------------------------------------------------------------------------
def build_model(num_classes: int, img_size: tuple = IMG_SIZE) -> keras.Model:
    """Build an EfficientNetB0-based transfer learning model."""
    base_model = tf.keras.applications.EfficientNetB0(
        include_top=False,
        weights="imagenet",
        input_shape=(*img_size, 3),
    )
    base_model.trainable = False  # Freeze all base layers for Phase 1

    inputs = keras.Input(shape=(*img_size, 3))
    x = base_model(inputs, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(256, activation="relu")(x)
    x = layers.Dropout(0.5)(x)
    # Ensure float32 output for numerical stability with mixed precision
    outputs = layers.Dense(num_classes, activation="softmax", dtype="float32")(x)

    model = keras.Model(inputs, outputs)
    return model, base_model


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------
def get_callbacks(phase: str = "phase1") -> list:
    """Return a list of training callbacks."""
    os.makedirs(MODEL_DIR, exist_ok=True)
    return [
        callbacks.EarlyStopping(
            monitor="val_accuracy", patience=3, restore_best_weights=True, verbose=1
        ),
        callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=2, min_lr=1e-7, verbose=1
        ),
        callbacks.ModelCheckpoint(
            MODEL_PATH, monitor="val_accuracy", save_best_only=True, verbose=1
        ),
    ]


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------
def evaluate_model(model: keras.Model, val_generator, class_names: list):
    """Print accuracy, confusion matrix and classification report."""
    print("\n" + "=" * 60)
    print("EVALUATION")
    print("=" * 60)

    # Evaluate
    loss, acc = model.evaluate(val_generator, verbose=0)
    print(f"\nValidation Loss : {loss:.4f}")
    print(f"Validation Accuracy: {acc:.4f}  ({acc * 100:.1f}%)")

    # Predictions
    val_generator.reset()
    y_pred_probs = model.predict(val_generator, verbose=0)
    y_pred = np.argmax(y_pred_probs, axis=1)
    y_true = val_generator.classes[: len(y_pred)]

    # Classification report
    print("\n--- Classification Report ---")
    print(classification_report(y_true, y_pred, target_names=class_names, zero_division=0))

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    print("--- Confusion Matrix ---")
    print(cm)

    return acc


# ---------------------------------------------------------------------------
# TFLite conversion
# ---------------------------------------------------------------------------
def convert_to_tflite(model_path: str = MODEL_PATH, output_path: str = TFLITE_PATH):
    """Convert the saved Keras model to a quantized TFLite model."""
    print("\n[INFO] Converting model to TensorFlow Lite ...")
    model = keras.models.load_model(model_path)
    converter = tf.lite.TFLiteConverter.from_keras_model(model)

    # Post-training dynamic range quantization
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_types = [tf.float16]

    tflite_model = converter.convert()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(tflite_model)

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"[INFO] TFLite model saved to {output_path} ({size_mb:.1f} MB)")


# ---------------------------------------------------------------------------
# Main training loop
# ---------------------------------------------------------------------------
def train(dataset_dir: str, batch_size: int, skip_tflite: bool = False):
    """Full two-phase training pipeline."""
    setup_gpu()

    # ── Data ──────────────────────────────────────────────────────────
    print(f"\n[INFO] Loading dataset from: {dataset_dir}")
    train_gen, val_gen, class_names = create_data_generators(dataset_dir, batch_size=batch_size)
    num_classes = len(class_names)
    print(f"[INFO] Found {num_classes} classes: {class_names[:10]}{'...' if num_classes > 10 else ''}")
    print(f"[INFO] Training samples : {train_gen.samples}")
    print(f"[INFO] Validation samples: {val_gen.samples}")

    # Save class names for inference
    os.makedirs(MODEL_DIR, exist_ok=True)
    with open(CLASS_NAMES_PATH, "w") as f:
        json.dump(class_names, f, indent=2)
    print(f"[INFO] Class names saved to {CLASS_NAMES_PATH}")

    # ── Build model ───────────────────────────────────────────────────
    model, base_model = build_model(num_classes)
    model.summary(print_fn=lambda x: print(x))

    # ── Phase 1: Train top layers ─────────────────────────────────────
    print("\n" + "=" * 60)
    print("PHASE 1: Training top layers (base frozen)")
    print("=" * 60)

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=PHASE1_LR),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=PHASE1_EPOCHS,
        callbacks=get_callbacks("phase1"),
    )

    # ── Phase 2: Fine-tune ────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"PHASE 2: Fine-tuning (unfreezing from layer {FINE_TUNE_AT})")
    print("=" * 60)

    base_model.trainable = True
    for layer in base_model.layers[:FINE_TUNE_AT]:
        layer.trainable = False

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=PHASE2_LR),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=PHASE2_EPOCHS,
        callbacks=get_callbacks("phase2"),
    )

    # ── Evaluation ────────────────────────────────────────────────────
    # Load the best checkpoint
    model = keras.models.load_model(MODEL_PATH)
    acc = evaluate_model(model, val_gen, class_names)

    # ── TFLite conversion ─────────────────────────────────────────────
    if not skip_tflite:
        convert_to_tflite()

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print(f"  Best model   : {MODEL_PATH}")
    if not skip_tflite:
        print(f"  TFLite model : {TFLITE_PATH}")
    print(f"  Class names  : {CLASS_NAMES_PATH}")
    print(f"  Val accuracy : {acc * 100:.1f}%")
    print("=" * 60)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="SmartFarm AI - Train crop disease classifier")
    parser.add_argument(
        "--dataset",
        type=str,
        default=DEFAULT_DATASET_DIR,
        help=f"Path to dataset directory (default: {DEFAULT_DATASET_DIR})",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help=f"Batch size (default: {BATCH_SIZE})",
    )
    parser.add_argument(
        "--skip-tflite",
        action="store_true",
        help="Skip TFLite conversion after training",
    )
    parser.add_argument(
        "--convert-only",
        action="store_true",
        help="Only convert existing .h5 model to TFLite (no training)",
    )
    args = parser.parse_args()

    if args.convert_only:
        convert_to_tflite()
    else:
        train(args.dataset, args.batch_size, args.skip_tflite)


if __name__ == "__main__":
    main()
