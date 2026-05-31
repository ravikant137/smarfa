"""
Vision Transformer (ViT) Pathogen Disease Classifier
"""

import logging
import torch
import torch.nn as nn

logger = logging.getLogger(__name__)

class DiseaseViT(nn.Module):
    def __init__(
        self, 
        num_classes: int, 
        pretrained: bool = True, 
        img_size: int = 224, 
        patch_size: int = 16
    ):
        super(DiseaseViT, self).__init__()
        self.num_classes = num_classes
        self.vit = None
        self._initialize_transformer(pretrained, img_size, patch_size)

    def _initialize_transformer(self, pretrained: bool, img_size: int, patch_size: int):
        try:
            from timm.models.vision_transformer import VisionTransformer
            import timm
            
            # Construct standard ViT block
            self.vit = VisionTransformer(
                img_size=img_size,
                patch_size=patch_size,
                embed_dim=768,
                depth=12,
                num_heads=12,
                mlp_ratio=4,
                qkv_bias=True,
                num_classes=self.num_classes
            )
            
            if pretrained:
                pretrained_model = timm.create_model('vit_base_patch16_224', pretrained=True)
                self.vit.load_state_dict(pretrained_model.state_dict(), strict=False)
                # Freeze early self-attention blocks
                for param in self.vit.blocks[:-2].parameters():
                    param.requires_grad = False
            logger.info("[DiseaseViT] Vision Transformer compiled successfully.")
        except Exception as e:
            logger.warning(f"[DiseaseViT] timm library/ViT load failed: {e}. Fallback active.")
            # Self-contained lightweight fallback CNN model for local development environments
            self.vit = nn.Sequential(
                nn.Conv2d(3, 32, kernel_size=3, padding=1),
                nn.ReLU(),
                nn.MaxPool2d(2, 2),
                nn.AdaptiveAvgPool2d((1, 1)),
                nn.Flatten(),
                nn.Linear(32, self.num_classes)
            )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.vit(x)
