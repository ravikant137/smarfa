import torch
import torch.nn as nn
try:
    import timm
    from peft import LoraConfig, get_peft_model
except ImportError:
    timm = None
    peft = None

class MultiTaskModel(nn.Module):
    def __init__(self, backbone_name='efficientnet_v2_s', num_species=2959, num_binary=2, lora_r=8):
        super(MultiTaskModel, self).__init__()
        
        if timm is None:
            raise ImportError("timm and peft are required for this model.")
            
        # Create backbone
        self.backbone = timm.create_model(backbone_name, pretrained=True, num_classes=0, global_pool='avg')
        
        # Apply LoRA if r > 0
        if lora_r > 0:
            config = LoraConfig(
                r=lora_r,
                lora_alpha=32,
                target_modules=["blocks.*.attention.qkv", "blocks.*.attention.proj"] if "swin" in backbone_name else ["conv_pw", "conv_pwl"],
                lora_dropout=0.05,
                bias="none"
            )
            self.backbone = get_peft_model(self.backbone, config)
            print(f"Applied LoRA (r={lora_r}) to {backbone_name}")

        # Task heads
        backbone_out_features = self._get_backbone_out_features(backbone_name)
        
        self.species_head = nn.Sequential(
            nn.Linear(backbone_out_features, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, num_species)
        )
        
        self.binary_head = nn.Sequential(
            nn.Linear(backbone_out_features, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, num_binary)
        )

    def _get_backbone_out_features(self, name):
        # Determine feature size based on architecture
        if 'efficientnet_v2_s' in name:
            return 1280
        if 'swin_tiny' in name:
            return 768
        # Fallback to a probe
        return 1280 

    def forward(self, x):
        features = self.backbone(x)
        species_logits = self.species_head(features)
        binary_logits = self.binary_head(features)
        return species_logits, binary_logits

def create_crop_weed_model(backbone='efficientnet_v2_s', lora_r=8):
    model = MultiTaskModel(backbone_name=backbone, lora_r=lora_r)
    return model

if __name__ == "__main__":
    # Test model creation and forward pass
    try:
        model = create_crop_weed_model(backbone='efficientnet_v2_s', lora_r=8)
        dummy_input = torch.randn(1, 3, 224, 224)
        species, binary = model(dummy_input)
        print(f"Species output shape: {species.shape}")
        print(f"Binary output shape: {binary.shape}")
    except Exception as e:
        print(f"Initialization failed (likely due to missing packages): {e}")
