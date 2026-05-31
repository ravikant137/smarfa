"""
Production Agriculture AI - Core Configuration Constants
"""

import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data_pipeline"
MODELS_DIR = BASE_DIR / "ml_models"
TRAINING_DIR = BASE_DIR / "training_pipeline"
RECOMMENDATIONS_DIR = BASE_DIR / "geo_recommendations"

# Model Hyperparameters
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
NUM_EPOCHS = 30
LEARNING_RATE = 1e-4
WEIGHT_DECAY = 1e-5

# Confidence Threshold Engine Parameters
MIN_CONFIDENCE_THRESHOLD = 0.65
MIN_BLUR_THRESHOLD = 85.0
MIN_CONTRAST = 35.0

# Supported Crops & Diseases lists
SUPPORTED_CROPS = [
    "Apple", "Blueberry", "Cherry", "Corn", "Grape", 
    "Orange", "Peach", "Pepper", "Potato", "Raspberry", 
    "Soybean", "Squash", "Strawberry", "Tomato", "Wheat"
]

SUPPORTED_DISEASES = [
    "Scab", "Black Rot", "Cedar Apple Rust", "Powdery Mildew",
    "Cercospora Leaf Spot (Gray Leaf Spot)", "Common Rust",
    "Northern Leaf Blight", "Huanglongbing (Citrus Greening)",
    "Bacterial Spot", "Early Blight", "Late Blight", "Leaf Mold",
    "Septoria Leaf Spot", "Spider Mites (Two-Spotted Spider Mite)",
    "Target Spot", "Yellow Leaf Curl Virus", "Mosaic Virus",
    "Leaf Scorch", "Brown Streak Disease", "Green Mottle Disease",
    "Stripe Rust", "Leaf Rust", "Healthy"
]
