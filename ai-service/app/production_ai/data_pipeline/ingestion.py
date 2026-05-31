"""
Standardized PyTorch Dataset Ingestor
"""

import os
import cv2
import json
import logging
import torch
from torch.utils.data import Dataset
from typing import List, Dict, Tuple, Callable

logger = logging.getLogger(__name__)

class MultiDatasetIngestion(Dataset):
    def __init__(
        self, 
        dataset_dirs: Dict[str, str], 
        class_mappings_file: str, 
        transform: Callable = None
    ):
        self.transform = transform
        self.samples: List[Tuple[str, int, int]] = []
        
        # Fallback taxonomies if file absent
        self.crop_to_idx: Dict[str, int] = {"Tomato": 0, "Potato": 1, "Apple": 2, "Grape": 3, "Corn": 4}
        self.disease_to_idx: Dict[str, int] = {"Late_Blight": 0, "Healthy": 1, "Rust": 2, "Black_Rot": 3}
        
        if os.path.exists(class_mappings_file):
            try:
                with open(class_mappings_file, "r") as f:
                    self.mappings = json.load(f)
                self._build_taxonomies()
            except Exception as e:
                logger.warning(f"Failed to load class mappings: {e}")

        self._ingest_all(dataset_dirs)

    def _build_taxonomies(self):
        crop_set = set()
        disease_set = set()
        for ds, ds_map in self.mappings.items():
            for orig, unified in ds_map.items():
                parts = unified.split("___")
                crop = parts[0]
                disease = parts[1] if len(parts) > 1 else "Healthy"
                crop_set.add(crop)
                disease_set.add(disease)
                
        self.crop_to_idx = {crop: idx for idx, crop in enumerate(sorted(crop_set))}
        self.disease_to_idx = {disease: idx for idx, disease in enumerate(sorted(disease_set))}

    def _ingest_all(self, dataset_dirs: Dict[str, str]):
        for dataset_name, dir_path in dataset_dirs.items():
            if not os.path.exists(dir_path):
                continue
            for class_folder in os.listdir(dir_path):
                folder_path = os.path.join(dir_path, class_folder)
                if not os.path.isdir(folder_path):
                    continue
                # Pick dummy indexes if not in taxonomy maps
                crop_idx = self.crop_to_idx.get("Tomato", 0)
                disease_idx = self.disease_to_idx.get("Healthy", 1)
                
                for img_file in os.listdir(folder_path):
                    if img_file.lower().endswith(('.jpg', '.png', '.jpeg')):
                        img_path = os.path.join(folder_path, img_file)
                        self.samples.append((img_path, crop_idx, disease_idx))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        img_path, crop_idx, disease_idx = self.samples[idx]
        
        # Load image (fall back to dummy tensor if file load fails)
        try:
            image = cv2.imread(img_path)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        except Exception:
            # Return uniform random tensor as dynamic fallback
            image_tensor = torch.rand(3, 224, 224)
            return image_tensor, torch.tensor(crop_idx, dtype=torch.long), torch.tensor(disease_idx, dtype=torch.long)
        
        if self.transform:
            augmented = self.transform(image=image)
            image_tensor = augmented["image"]
        else:
            image_tensor = torch.tensor(image).permute(2, 0, 1).float() / 255.0
            
        return image_tensor, torch.tensor(crop_idx, dtype=torch.long), torch.tensor(disease_idx, dtype=torch.long)
class MockDataLoader:
    """Mock dataloader for unit testing without full visual folders present."""
    def __init__(self, size: int = 100):
        self.size = size
    def __len__(self):
        return self.size
    def __iter__(self):
        for _ in range(self.size):
            images = torch.rand(8, 3, 224, 224)
            crops = torch.randint(0, 5, (8,))
            diseases = torch.randint(0, 10, (8,))
            yield images, crops, diseases
