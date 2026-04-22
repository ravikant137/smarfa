import os
import time
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.cuda.amp import GradScaler, autocast
import argparse
from tqdm import tqdm
from pytorch_data import get_dataloaders
from model_factory import create_crop_weed_model

def save_metrics(epoch, train_loss, val_acc_bin, val_acc_spec, status='active'):
    metrics = {
        "status": status,
        "epoch": epoch,
        "train_loss": train_loss,
        "val_accuracy_binary": val_acc_bin,
        "val_accuracy_species": val_acc_spec
    }
    with open("metrics.json", "w") as f:
        json.dump(metrics, f)

def train(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on {device}")
    
    # Data
    train_loader, val_loader = get_dataloaders(batch_size=args.batch_size)
    if train_loader is None:
        return
        
    # Model
    model = create_crop_weed_model(backbone=args.backbone, lora_r=args.lora_r)
    model.to(device)
    
    # Multi-task losses
    species_criterion = nn.CrossEntropyLoss()
    binary_criterion = nn.CrossEntropyLoss()
    
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingWarmRestarts(optimizer, T_0=10)
    scaler = GradScaler() # For Mixed Precision
    
    history = {"loss": [], "bin_acc": [], "spec_acc": []}
    
    for epoch in range(args.epochs):
        model.train()
        running_loss = 0.0
        pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{args.epochs}")
        
        optimizer.zero_grad()
        
        for i, batch in enumerate(pbar):
            images = batch['image'].to(device)
            species_targets = batch['species_label'].to(device)
            binary_targets = batch['binary_label'].to(device)
            
            with autocast(): # Mixed Precision
                species_logits, binary_logits = model(images)
                
                loss_species = species_criterion(species_logits, species_targets)
                loss_binary = binary_criterion(binary_logits, binary_targets)
                
                # Weighted multi-task loss
                loss = (args.alpha * loss_species) + ((1 - args.alpha) * loss_binary)
                loss = loss / args.accumulation_steps

            scaler.scale(loss).backward()
            
            if (i + 1) % args.accumulation_steps == 0:
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad()
                
            running_loss += loss.item() * args.accumulation_steps
            pbar.set_postfix({'loss': running_loss / (i + 1)})
            
        # Validation
        model.eval()
        bin_correct = 0
        spec_correct = 0
        total = 0
        
        with torch.no_grad():
            for batch in val_loader:
                images = batch['image'].to(device)
                species_targets = batch['species_label'].to(device)
                binary_targets = batch['binary_label'].to(device)
                
                species_logits, binary_logits = model(images)
                
                _, spec_preds = torch.max(species_logits, 1)
                _, bin_preds = torch.max(binary_logits, 1)
                
                total += species_targets.size(0)
                spec_correct += (spec_preds == species_targets).sum().item()
                bin_correct += (bin_preds == binary_targets).sum().item()
        
        epoch_loss = running_loss / len(train_loader)
        epoch_bin_acc = bin_correct / total
        epoch_spec_acc = spec_correct / total
        
        history["loss"].append(epoch_loss)
        history["bin_acc"].append(epoch_bin_acc)
        history["spec_acc"].append(epoch_spec_acc)
        
        print(f"Epoch {epoch+1}: Loss {epoch_loss:.4f} | Bin Acc {epoch_bin_acc:.4f} | Spec Acc {epoch_spec_acc:.4f}")
        
        save_metrics(epoch + 1, history["loss"], history["bin_acc"], history["spec_acc"])
        scheduler.step()
        
        # Save checkpoint
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'loss': epoch_loss,
        }, f"checkpoint_epoch_{epoch+1}.pt")

    save_metrics(args.epochs, history["loss"], history["bin_acc"], history["spec_acc"], status='done')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--backbone", type=str, default="efficientnet_v2_s")
    parser.add_argument("--lora-r", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=8) # Small for 2GB GPU
    parser.add_argument("--accumulation-steps", type=int, default=4)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--alpha", type=float, default=0.5, help="Weight for species loss")
    args = parser.parse_args()
    
    train(args)
