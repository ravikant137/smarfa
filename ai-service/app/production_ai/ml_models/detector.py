"""
YOLOv8 Bounding Box Leaf and Crop Detector Wrapper
"""

import cv2
import logging
import numpy as np
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

class FieldObjectDetector:
    def __init__(self, model_weights_path: str = "best_yolov8.pt"):
        self.weights_path = model_weights_path
        self.model = None
        self._load_yolo()

    def _load_yolo(self):
        try:
            from ultralytics import YOLO
            if os.path.exists(self.weights_path):
                self.model = YOLO(self.weights_path)
                logger.info("[Detector] Successfully loaded YOLOv8 model weights.")
        except ImportError:
            logger.warning("[Detector] Ultralytics not installed. Leaf detection fallback active.")
        except Exception as e:
            logger.warning(f"[Detector] Failed to initialize YOLOv8: {e}. Fallback active.")

    def detect_leaf_zone(
        self, 
        image_bytes: bytes, 
        confidence_threshold: float = 0.45
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Locates the leaf/crop in the frame, removing background noise.
        
        If YOLOv8 is not loaded, gracefully falls back to center-cropping.
        """
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None:
            # Create a uniform fallback blank image
            img = np.zeros((224, 224, 3), dtype=np.uint8)
            
        h, w, _ = img.shape
        
        # 1. Run YOLO inference if model is loaded
        if self.model is not None:
            try:
                results = self.model(img, verbose=False)[0]
                best_box = None
                best_conf = 0.0
                
                for box in results.boxes:
                    conf = float(box.conf[0])
                    if conf > confidence_threshold and conf > best_conf:
                        best_conf = conf
                        best_box = box.xyxy[0].cpu().numpy().astype(int)
                        
                if best_box is not None:
                    x1, y1, x2, y2 = best_box
                    pad_x = int((x2 - x1) * 0.1)
                    pad_y = int((y2 - y1) * 0.1)
                    
                    x1_pad = max(0, x1 - pad_x)
                    y1_pad = max(0, y1 - pad_y)
                    x2_pad = min(w, x2 + pad_x)
                    y2_pad = min(h, y2 + pad_y)
                    
                    cropped_image = img[y1_pad:y2_pad, x1_pad:x2_pad]
                    return cropped_image, {
                        "detected": True,
                        "confidence": best_conf,
                        "bbox": [x1_pad, y1_pad, x2_pad, y2_pad]
                    }
            except Exception as e:
                logger.warning(f"[Detector] Inference exception: {e}")

        # 2. Fallback: Crop center 80% area
        logger.info("[Detector] Applying standard 80% visual center crop.")
        cx, cy = w // 2, h // 2
        cw, ch = int(w * 0.8), int(h * 0.8)
        x1 = max(0, cx - cw // 2)
        y1 = max(0, cy - ch // 2)
        x2 = min(w, cx + cw // 2)
        y2 = min(h, cy + ch // 2)
        
        cropped_image = img[y1:y2, x1:x2]
        return cropped_image, {
            "detected": False,
            "confidence": 0.0,
            "bbox": [x1, y1, x2, y2]
        }
