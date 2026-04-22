import os
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
import numpy as np

try:
    import agml
except ImportError:
    agml = None

class iNatAgDataset(Dataset):
    def __init__(self, data_list, transform=None):
        """
        data_list: list of tuples (image_path, species_label, binary_label)
        """
        self.data_list = data_list
        self.transform = transform

    def __len__(self):
        return len(self.data_list)

    def __getitem__(self, idx):
        img_path, species_label, binary_label = self.data_list[idx]
        image = Image.open(img_path).convert('RGB')
        
        if self.transform:
            image = self.transform(image)
            
        return {
            'image': image,
            'species_label': torch.tensor(species_label, dtype=torch.long),
            'binary_label': torch.tensor(binary_label, dtype=torch.long)
        }

def get_dataloaders(batch_size=16, subset_size=None):
    if agml is None:
        print("AgML not found. Please install it first.")
        return None, None

    print("Loading iNatAg-mini dataset...")
    # AgML manages the download and loading
    loader = agml.data.AgMLDataLoader.from_parent("iNatAg-mini")
    
    # Extract images and labels
    all_images = loader.images
    all_labels = loader.labels 
    # In iNatAg, labels usually come as species IDs. 
    # We need to map them to binary (Crop vs Weed).
    # AgML metadata provides this mapping.
    
    metadata = loader.info
    # Assume metadata has "class_type" or similar (Crop/Weed)
    # For now, let's derive it from the species index if possible or use a placeholder map
    # A real implementation would use: metadata.class_to_type
    
    # Placeholder: Assuming first 1986 are crops, rest are weeds based on research
    # We should use actual agml metadata if available
    class_map = {} # species_id -> 0 (crop) or 1 (weed)
    # loader.info.class_names might help
    
    data_list = []
    # This is a simplification. Real AgMLDataLoader has a internal list.
    # We'll use the internal structure if we can probe it.
    
    # For now, let's implement a robust version that handles the split
    train_loader, val_loader = loader.split(train=0.8, val=0.2)
    
    # Wrap them in Torch
    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(0.2, 0.2, 0.2),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    # Note: AgML loaders can be directly used, but for LoRA/multi-task, 
    # we might need custom wrappers if AgML doesn't provide both labels together.
    
    # Returning AgML loaders for now as they are very capable
    # and we can wrap them in a simple torch-compatible way.
    return train_loader, val_loader

if __name__ == "__main__":
    # Test loading
    train, val = get_dataloaders()
    if train:
        print(f"Loaded {len(train)} training samples.")
