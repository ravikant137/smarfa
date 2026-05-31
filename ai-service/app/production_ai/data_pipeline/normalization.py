"""
Unified Taxonomic Label Normalizer for Agriculture Datasets
"""

import json
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

UNIFIED_CLASS_MAP = {
    "tomato": "Tomato",
    "potato": "Potato",
    "apple": "Apple",
    "maize": "Corn",
    "corn": "Corn",
    "grape": "Grape",
    "rice": "Rice",
    "paddy": "Rice",
    "cassava": "Cassava",
    "blueberry": "Blueberry",
    "cherry": "Cherry",
    "peach": "Peach",
    "pepper": "Pepper",
    "squash": "Squash",
    "strawberry": "Strawberry",
    
    "scab": "Scab",
    "black_rot": "Black Rot",
    "blackrot": "Black Rot",
    "rust": "Rust",
    "early_blight": "Early Blight",
    "earlyblight": "Early Blight",
    "late_blight": "Late Blight",
    "lateblight": "Late Blight",
    "powdery_mildew": "Powdery Mildew",
    "mildew": "Powdery Mildew",
    "bacterial_spot": "Bacterial Spot",
    "leaf_scorch": "Leaf Scorch",
    "yellow_leaf_curl": "Yellow Leaf Curl Virus",
    "mosaic_virus": "Mosaic Virus",
    "brown_spot": "Brown Spot",
    "hispa": "Hispa",
    "blast": "Blast",
    "bacterial_blight": "Bacterial Blight",
    "brown_streak": "Brown Streak Disease",
    "green_mottle": "Green Mottle Disease",
}

class DatasetNormalizer:
    def __init__(self, output_mappings_path: str = "class_mappings.json"):
        self.output_mappings_path = output_mappings_path
        self.registry: Dict[str, Dict[str, str]] = {}

    def normalize_label(self, raw_label: str) -> Tuple[str, str]:
        """Normalize dataset labels to (Crop, Disease) schema."""
        raw_clean = raw_label.lower().replace("-", "_").replace(" ", "_")
        parts = raw_clean.split("___") if "___" in raw_clean else raw_clean.split("_")
        
        detected_crop = "Unknown"
        detected_disease = "Healthy"
        
        for part in parts:
            for key, crop_val in UNIFIED_CLASS_MAP.items():
                if key in part:
                    detected_crop = crop_val
                    break
        
        for key, disease_val in UNIFIED_CLASS_MAP.items():
            if key in raw_clean:
                detected_disease = disease_val
                if "healthy" in raw_clean:
                    detected_disease = "Healthy"
                break
                
        return detected_crop, detected_disease

    def register_dataset(self, dataset_name: str, class_list: List[str]) -> Dict[str, str]:
        dataset_mappings = {}
        for original in class_list:
            crop, disease = self.normalize_label(original)
            unified = f"{crop}___{disease.replace(' ', '_')}"
            dataset_mappings[original] = unified
            logger.info(f"[{dataset_name}] Registered: '{original}' -> '{unified}'")
            
        self.registry[dataset_name] = dataset_mappings
        return dataset_mappings
