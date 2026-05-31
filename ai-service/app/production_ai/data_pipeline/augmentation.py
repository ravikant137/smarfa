"""
Field-Robust Environmental Augmentation Pipeline
"""

from typing import Tuple

try:
    import albumentations as A
    from albumentations.pytorch import ToTensorV2
    HAS_ALBUMENTATIONS = True
except ImportError:
    HAS_ALBUMENTATIONS = False

def get_field_robust_augmentation(img_size: Tuple[int, int] = (224, 224)):
    """Production augmentation pipeline simulating real-world agricultural conditions."""
    if not HAS_ALBUMENTATIONS:
        # Graceful fallback transformer if albumentations is absent
        class SimpleFallbackTransform:
            def __call__(self, image):
                import torch
                # Simple cv2 to pytorch float tensor mapping
                tensor = torch.tensor(image).permute(2, 0, 1).float() / 255.0
                return {"image": tensor}
        return SimpleFallbackTransform()

    return A.Compose([
        A.RandomResizedCrop(height=img_size[0], width=img_size[1], scale=(0.7, 1.0), p=1.0),
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.3),
        A.RandomRotate90(p=0.5),
        A.ShiftScaleRotate(shift_limit=0.1, scale_limit=0.15, rotate_limit=30, border_mode=0, p=0.7),
        
        A.OneOf([
            A.MotionBlur(blur_limit=7, p=1.0),
            A.GaussianBlur(blur_limit=5, p=1.0),
        ], p=0.4),
        
        A.RandomBrightnessContrast(brightness_limit=(-0.25, 0.25), contrast_limit=(-0.2, 0.2), p=0.8),
        A.HueSaturationValue(hue_shift_limit=15, sat_shift_limit=20, val_shift_limit=15, p=0.5),
        
        A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        ToTensorV2(),
    ])
