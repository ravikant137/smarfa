"""
EfficientNetV2 Crop Species Classifier Neural Network
"""

import logging
import torch
import torch.nn as nn

logger = logging.getLogger(__name__)

class CropClassifierNet(nn.Module):
    def __init__(self, num_classes: int, pretrained: bool = True):
        super(CropClassifierNet, self).__init__()
        self.num_classes = num_classes
        self.backbone = None
        self._initialize_backbone(pretrained)

    def _initialize_backbone(self, pretrained: bool):
        try:
            import torchvision.models as models
            weights = models.EfficientNet_V2_S_Weights.DEFAULT if pretrained else None
            self.backbone = models.efficientnet_v2_s(weights=weights)
            
            # Freeze shallow feature extraction layers
            for param in list(self.backbone.parameters())[:-30]:
                param.requires_grad = False
                
            in_features = self.backbone.classifier[1].in_features
            self.backbone.classifier = nn.Sequential(
                nn.Dropout(p=0.3, inplace=True),
                nn.Linear(in_features, 256),
                nn.SiLU(),
                nn.BatchNorm1d(256),
                nn.Dropout(p=0.2),
                nn.Linear(256, self.num_classes)
            )
            logger.info("[CropClassifier] Initialized EfficientNetV2 Backbone successfully.")
        except Exception as e:
            logger.warning(f"[CropClassifier] Failed loading EfficientNetV2 backbone: {e}. Fallback active.")
            # Self-contained lightweight fallback CNN model
            self.backbone = nn.Sequential(
                nn.Conv2d(3, 16, kernel_size=3, padding=1),
                nn.ReLU(),
                nn.MaxPool2d(2, 2),
                nn.AdaptiveAvgPool2d((1, 1)),
                nn.Flatten(),
                nn.Linear(16, self.num_classes)
            )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)
