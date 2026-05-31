"""
GPU-Optimized Automatic Mixed Precision (AMP) Training Loop
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.cuda.amp import autocast, GradScaler
from torch.utils.data import DataLoader
from typing import Tuple

def train_one_epoch(
    model: nn.Module, 
    dataloader: DataLoader, 
    optimizer: optim.Optimizer, 
    criterion: nn.Module, 
    device: torch.device, 
    scaler: GradScaler
) -> Tuple[float, float]:
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    for batch_idx, (images, crops, diseases) in enumerate(dataloader):
        images, crops, diseases = images.to(device), crops.to(device), diseases.to(device)
        optimizer.zero_grad()
        
        # Mixed Precision Autocasting
        with autocast(enabled=(device.type == 'cuda')):
            outputs = model(images)
            loss = criterion(outputs, diseases)
            
        # Scaled backward pass
        if device.type == 'cuda':
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            scaler.step(optimizer)
            scaler.update()
        else:
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
        
        running_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        total += diseases.size(0)
        correct += predicted.eq(diseases).sum().item()
        
    epoch_loss = running_loss / total
    epoch_acc = correct / total
    return epoch_loss, epoch_acc
