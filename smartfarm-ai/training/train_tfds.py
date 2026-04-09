"""
SmartFarm AI - Train directly from TensorFlow Datasets (PlantVillage)
Optimized for CPU training with EfficientNetB0.
Targets >95% validation accuracy.
"""

import os
import sys
import json
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, callbacks
import tensorflow_datasets as tfds

# Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(PROJECT_ROOT, "model")
MODEL_PATH = os.path.join(MODEL_DIR, "smartfarm_model.h5")
TFLITE_PATH = os.path.join(MODEL_DIR, "smartfarm_model.tflite")
CLASS_NAMES_PATH = os.path.join(MODEL_DIR, "class_names.json")

IMG_SIZE = 160  # Smaller for faster CPU training; MobileNetV2 handles this well
BATCH_SIZE = 32
AUTOTUNE = tf.data.AUTOTUNE


def preprocess_train(image, label):
    """Training preprocessing with augmentation."""
    image = tf.cast(image, tf.float32)
    image = tf.image.resize(image, [IMG_SIZE, IMG_SIZE])
    # Augmentation
    image = tf.image.random_flip_left_right(image)
    image = tf.image.random_flip_up_down(image)
    image = tf.image.random_brightness(image, 0.2)
    image = tf.image.random_contrast(image, 0.8, 1.2)
    image = tf.image.random_saturation(image, 0.8, 1.2)
    # Random rotation via random crop + resize
    image = tf.image.resize_with_crop_or_pad(image, IMG_SIZE + 30, IMG_SIZE + 30)
    image = tf.image.random_crop(image, [IMG_SIZE, IMG_SIZE, 3])
    image = image / 255.0
    image = tf.clip_by_value(image, 0.0, 1.0)
    return image, label


def preprocess_val(image, label):
    """Validation preprocessing (no augmentation)."""
    image = tf.cast(image, tf.float32)
    image = tf.image.resize(image, [IMG_SIZE, IMG_SIZE])
    image = image / 255.0
    return image, label


def load_dataset():
    """Load PlantVillage from tfds and split into train/val."""
    print("[INFO] Loading PlantVillage from tensorflow_datasets...")
    
    ds, info = tfds.load(
        'plant_village',
        split='train',
        with_info=True,
        as_supervised=True,
    )
    
    num_classes = info.features['label'].num_classes
    class_names = info.features['label'].names
    total_examples = info.splits['train'].num_examples
    
    print(f"[INFO] Dataset: {total_examples} images, {num_classes} classes")
    
    # Split 80/20
    val_size = int(total_examples * 0.2)
    train_size = total_examples - val_size
    
    ds = ds.shuffle(total_examples, seed=42)
    train_ds = ds.take(train_size)
    val_ds = ds.skip(train_size)
    
    # Apply preprocessing with caching for speed
    train_ds = (
        train_ds
        .cache()
        .map(preprocess_train, num_parallel_calls=AUTOTUNE)
        .batch(BATCH_SIZE)
        .prefetch(AUTOTUNE)
    )
    
    val_ds = (
        val_ds
        .cache()
        .map(preprocess_val, num_parallel_calls=AUTOTUNE)
        .batch(BATCH_SIZE)
        .prefetch(AUTOTUNE)
    )
    
    return train_ds, val_ds, class_names, num_classes, train_size, val_size


def load_from_directory(dataset_dir):
    """Load from a directory structure (alternative to tfds)."""
    print(f"[INFO] Loading dataset from directory: {dataset_dir}")
    
    train_ds = tf.keras.utils.image_dataset_from_directory(
        dataset_dir,
        validation_split=0.2,
        subset="training",
        seed=42,
        image_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        label_mode='int',
    )
    
    val_ds = tf.keras.utils.image_dataset_from_directory(
        dataset_dir,
        validation_split=0.2,
        subset="validation",
        seed=42,
        image_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        label_mode='int',
    )
    
    class_names = train_ds.class_names
    num_classes = len(class_names)
    
    # Count samples from cardinality (fast) or estimate from file count
    total_files = sum(len(files) for _, _, files in os.walk(dataset_dir))
    train_size = int(total_files * 0.8)
    val_size = total_files - train_size
    
    print(f"[INFO] Found {num_classes} classes, {train_size} train, {val_size} val samples")
    
    # Augmentation for training
    data_augmentation = keras.Sequential([
        layers.RandomFlip("horizontal_and_vertical"),
        layers.RandomRotation(0.1),
        layers.RandomZoom(0.2),
        layers.RandomContrast(0.2),
    ])
    
    def augment_train(images, labels):
        images = data_augmentation(images, training=True)
        images = images / 255.0
        return images, labels
    
    def normalize_val(images, labels):
        images = images / 255.0
        return images, labels
    
    train_ds = train_ds.map(augment_train, num_parallel_calls=AUTOTUNE).prefetch(AUTOTUNE)
    val_ds = val_ds.map(normalize_val, num_parallel_calls=AUTOTUNE).prefetch(AUTOTUNE)
    
    return train_ds, val_ds, class_names, num_classes, train_size, val_size


def build_model(num_classes):
    """Build MobileNetV2 transfer learning model (fast on CPU)."""
    base_model = tf.keras.applications.MobileNetV2(
        include_top=False,
        weights="imagenet",
        input_shape=(IMG_SIZE, IMG_SIZE, 3),
    )
    base_model.trainable = False
    
    inputs = keras.Input(shape=(IMG_SIZE, IMG_SIZE, 3))
    x = base_model(inputs, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dense(256, activation="relu")(x)
    x = layers.Dropout(0.4)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)
    
    model = keras.Model(inputs, outputs)
    return model, base_model


def get_callbacks():
    os.makedirs(MODEL_DIR, exist_ok=True)
    return [
        callbacks.EarlyStopping(
            monitor="val_accuracy", patience=5, restore_best_weights=True, verbose=1
        ),
        callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=2, min_lr=1e-7, verbose=1
        ),
        callbacks.ModelCheckpoint(
            MODEL_PATH, monitor="val_accuracy", save_best_only=True, verbose=1
        ),
    ]


def convert_to_tflite():
    """Convert .h5 → quantized .tflite"""
    print("\n[INFO] Converting to TFLite with float16 quantization...")
    model = keras.models.load_model(MODEL_PATH)
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_types = [tf.float16]
    
    tflite_model = converter.convert()
    with open(TFLITE_PATH, "wb") as f:
        f.write(tflite_model)
    
    size_mb = os.path.getsize(TFLITE_PATH) / (1024 * 1024)
    print(f"[INFO] TFLite model saved: {TFLITE_PATH} ({size_mb:.1f} MB)")


def train():
    """Full training pipeline."""
    print("=" * 60)
    print("SmartFarm AI - Training Pipeline")
    print("=" * 60)
    
    # Try loading from directory first, then tfds
    dataset_dir = os.path.join(PROJECT_ROOT, "dataset")
    
    if os.path.exists(dataset_dir) and len([d for d in os.listdir(dataset_dir) if os.path.isdir(os.path.join(dataset_dir, d))]) > 5:
        train_ds, val_ds, class_names, num_classes, train_size, val_size = load_from_directory(dataset_dir)
    else:
        train_ds, val_ds, class_names, num_classes, train_size, val_size = load_dataset()
    
    # Save class names
    os.makedirs(MODEL_DIR, exist_ok=True)
    with open(CLASS_NAMES_PATH, "w") as f:
        json.dump(list(class_names), f, indent=2)
    print(f"[INFO] Saved {num_classes} class names to {CLASS_NAMES_PATH}")
    
    # Build model
    model, base_model = build_model(num_classes)
    model.summary()
    
    # ── Phase 1: Train top layers ─────────────────────────────────
    print("\n" + "=" * 60)
    print("PHASE 1: Training classification head (base frozen)")
    print("=" * 60)
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    
    history1 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=8,
        callbacks=get_callbacks(),
    )
    
    # ── Phase 2: Fine-tune ────────────────────────────────────────
    print("\n" + "=" * 60)
    print("PHASE 2: Fine-tuning (unfreezing last 30 layers)")
    print("=" * 60)
    
    base_model.trainable = True
    # Freeze all but last 40 layers (MobileNetV2 has ~155 layers)
    for layer in base_model.layers[:-40]:
        layer.trainable = False
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=5e-5),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    
    history2 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=10,
        callbacks=get_callbacks(),
    )
    
    # ── Evaluate ──────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("EVALUATION")
    print("=" * 60)
    
    model = keras.models.load_model(MODEL_PATH)
    loss, acc = model.evaluate(val_ds)
    print(f"\nFinal Validation Accuracy: {acc * 100:.2f}%")
    print(f"Final Validation Loss: {loss:.4f}")
    
    # ── TFLite conversion ─────────────────────────────────────────
    convert_to_tflite()
    
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print(f"  Model     : {MODEL_PATH}")
    print(f"  TFLite    : {TFLITE_PATH}")
    print(f"  Classes   : {CLASS_NAMES_PATH}")
    print(f"  Val Acc   : {acc * 100:.2f}%")
    print("=" * 60)
    
    return acc


if __name__ == "__main__":
    train()
