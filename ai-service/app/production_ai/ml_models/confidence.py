"""
Dynamic Contrast, Blur, and Probability Threshold Rejection Engine
"""

import cv2
import torch
import numpy as np
from typing import Dict, Any, Tuple

class QualityAndConfidenceEngine:
    def __init__(self, min_blur_threshold: float = 85.0, min_contrast: float = 35.0):
        self.min_blur_threshold = min_blur_threshold
        self.min_contrast = min_contrast

    def assess_image_quality(self, image_np: np.ndarray) -> Tuple[bool, str]:
        """Runs dynamic validation checks on the uploaded image.
        
        Returns:
            is_valid: True if image meets quality standards
            reason: Error detail string if rejected
        """
        try:
            gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
        except Exception:
            return False, "Invalid image format uploaded."
        
        # 1. Variance of Laplacian for motion blur detection
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        if blur_score < self.min_blur_threshold:
            return False, f"Image too blurry (Blur Score: {blur_score:.1f}). Focus and retake."
            
        # 2. Contrast detection via Min-Max boundaries
        contrast_score = float(gray.max() - gray.min())
        if contrast_score < self.min_contrast:
            return False, "Low contrast image detected. Adjust lighting and retake."
            
        # 3. Brightness/Exposure analysis
        mean_brightness = float(gray.mean())
        if mean_brightness < 25.0:
            return False, "Image too dark. Turn on flash or seek daylight."
        if mean_brightness > 240.0:
            return False, "Image overexposed. Avoid direct sunlight glare."
            
        return True, "Valid"

    def compute_decision(
        self, 
        crop_logits: torch.Tensor, 
        disease_logits: torch.Tensor, 
        threshold: float = 0.65
    ) -> Tuple[bool, float, Dict[str, Any]]:
        """Validates inference logit structures.
        
        If confidence drops below threshold, suppresses false prediction.
        """
        crop_probs = torch.softmax(crop_logits, dim=1)
        disease_probs = torch.softmax(disease_logits, dim=1)
        
        crop_conf, crop_idx = torch.max(crop_probs, dim=1)
        disease_conf, disease_idx = torch.max(disease_probs, dim=1)
        
        combined_score = float(crop_conf.item() * disease_conf.item())
        
        if combined_score < threshold:
            return False, combined_score, {
                "decision": "REJECT",
                "message": "Image unclear or unsupported crop leaf. Please provide a clearer close-up image of a supported crop leaf.",
                "confidence": combined_score
            }
            
        return True, combined_score, {
            "decision": "ACCEPT",
            "crop_idx": int(crop_idx.item()),
            "disease_idx": int(disease_idx.item()),
            "confidence": combined_score
        }
