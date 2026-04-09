"""
SmartFarm AI - Image Preprocessing Pipeline
Handles augmentation, normalization, and dataset loading for real-world farm conditions.
"""

import os
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
SEED = 42


# ---------------------------------------------------------------------------
# Custom noise / blur augmentation applied via preprocessing_function
# ---------------------------------------------------------------------------
def _add_noise_and_blur(image: np.ndarray) -> np.ndarray:
    """Randomly apply Gaussian noise and/or blur to a *single* image array
    (values expected in [0, 255] uint8 range, as delivered by Keras flow)."""
    img = image.copy()

    # Random Gaussian noise (50 % chance)
    if np.random.random() < 0.5:
        noise = np.random.normal(0, 12, img.shape).astype(np.float32)
        img = np.clip(img + noise, 0, 255)

    # Random blur (30 % chance) – convert through PIL
    if np.random.random() < 0.3:
        pil_img = Image.fromarray(img.astype(np.uint8))
        pil_img = pil_img.filter(ImageFilter.GaussianBlur(radius=np.random.uniform(0.5, 1.5)))
        img = np.array(pil_img, dtype=np.float32)

    return img


# ---------------------------------------------------------------------------
# Data generators
# ---------------------------------------------------------------------------
def create_data_generators(dataset_dir: str, batch_size: int = BATCH_SIZE, img_size: tuple = IMG_SIZE):
    """Return (train_generator, val_generator, class_names).

    The dataset directory should follow the Keras image_dataset_from_directory
    convention:
        dataset_dir/
            class_a/
                img1.jpg
                ...
            class_b/
                ...
    An 80/20 train-validation split is applied automatically.
    """

    train_datagen = ImageDataGenerator(
        rescale=1.0 / 255,
        rotation_range=30,
        width_shift_range=0.15,
        height_shift_range=0.15,
        zoom_range=(0.8, 1.3),
        brightness_range=(0.7, 1.3),
        horizontal_flip=True,
        vertical_flip=True,
        fill_mode="nearest",
        preprocessing_function=_add_noise_and_blur,
        validation_split=0.2,
    )

    val_datagen = ImageDataGenerator(
        rescale=1.0 / 255,
        validation_split=0.2,
    )

    train_generator = train_datagen.flow_from_directory(
        dataset_dir,
        target_size=img_size,
        batch_size=batch_size,
        class_mode="categorical",
        subset="training",
        seed=SEED,
        shuffle=True,
    )

    val_generator = val_datagen.flow_from_directory(
        dataset_dir,
        target_size=img_size,
        batch_size=batch_size,
        class_mode="categorical",
        subset="validation",
        seed=SEED,
        shuffle=False,
    )

    class_names = list(train_generator.class_indices.keys())
    return train_generator, val_generator, class_names


# ---------------------------------------------------------------------------
# Single-image preprocessing (used at inference time)
# ---------------------------------------------------------------------------
def preprocess_image(image_bytes: bytes, img_size: tuple = IMG_SIZE) -> np.ndarray:
    """Load an image from raw bytes and return a preprocessed numpy array
    ready for model prediction (batch dimension included)."""
    img = Image.open(__import__("io").BytesIO(image_bytes)).convert("RGB")
    img = img.resize(img_size, Image.LANCZOS)
    arr = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)


def preprocess_image_from_path(image_path: str, img_size: tuple = IMG_SIZE) -> np.ndarray:
    """Load an image from a file path and return a preprocessed numpy array."""
    img = Image.open(image_path).convert("RGB")
    img = img.resize(img_size, Image.LANCZOS)
    arr = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)


# ---------------------------------------------------------------------------
# TFLite preprocessing
# ---------------------------------------------------------------------------
def preprocess_image_tflite(image_bytes: bytes, img_size: tuple = IMG_SIZE) -> np.ndarray:
    """Preprocess for quantized TFLite model (float32 output)."""
    return preprocess_image(image_bytes, img_size)
