"""
SmartFarm AI - Image Preprocessing Pipeline
Handles advanced augmentation, normalization, and dataset loading for real-world farm conditions.
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
def _advanced_augmentation(image: np.ndarray) -> np.ndarray:
    """Randomly apply Gaussian noise, blur, contrast, and brightness to a *single* image array
    (values expected in [0, 255] uint8 range, as delivered by Keras flow)."""
    img = image.copy()
    
    # 1. Random contrast/brightness via PIL (40% chance)
    if np.random.random() < 0.4:
        pil_img = Image.fromarray(img.astype(np.uint8))
        if np.random.random() < 0.5:
            enhancer = ImageEnhance.Contrast(pil_img)
            pil_img = enhancer.enhance(np.random.uniform(0.7, 1.3))
        else:
            enhancer = ImageEnhance.Brightness(pil_img)
            pil_img = enhancer.enhance(np.random.uniform(0.8, 1.2))
        img = np.array(pil_img, dtype=np.float32)

    # 2. Random Gaussian noise (noisy backgrounds simulation) (50% chance)
    if np.random.random() < 0.5:
        noise = np.random.normal(0, np.random.uniform(5, 20), img.shape).astype(np.float32)
        img = np.clip(img + noise, 0, 255)

    # 3. Random blur (blur simulation) (30% chance)
    if np.random.random() < 0.3:
        pil_img = Image.fromarray(img.astype(np.uint8))
        pil_img = pil_img.filter(ImageFilter.GaussianBlur(radius=np.random.uniform(0.5, 2.0)))
        img = np.array(pil_img, dtype=np.float32)

    return img


# ---------------------------------------------------------------------------
# Data generators
# ---------------------------------------------------------------------------
def create_data_generators(dataset_dir: str, batch_size: int = BATCH_SIZE, img_size: tuple = IMG_SIZE):
    """Return (train_generator, val_generator, class_names)."""

    train_datagen = ImageDataGenerator(
        rescale=1.0 / 255,
        rotation_range=40,
        width_shift_range=0.2,
        height_shift_range=0.2,
        zoom_range=(0.7, 1.3),
        horizontal_flip=True,
        vertical_flip=True,
        fill_mode="reflect",
        preprocessing_function=_advanced_augmentation,
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
    
    # Optional central crop could be added here for better inference
    
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
