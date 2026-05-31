"""
Model Validation and Performance Evaluation Script
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from typing import Tuple

def evaluate_model(
    model: nn.Module, 
    dataloader: DataLoader, 
    criterion: nn.Module, 
    device: torch.device
) -> Tuple[float, float]:
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for images, crops, diseases in dataloader:
            images, crops, diseases = images.to(device), crops.to(device), diseases.to(device)
            outputs = model(images)
            loss = criterion(outputs, diseases)
            
            running_loss += loss.item() * images.size(0)
            _, predicted = outputs.max(1)
            total += diseases.size(0)
            correct += predicted.eq(diseases).sum().item()
            
    val_loss = running_loss / total
    val_acc = correct / total
    return val_loss, val_acc
