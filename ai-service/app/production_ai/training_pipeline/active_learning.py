"""
Active Learning and Expert Validation retrainer logic
"""

import os
import shutil
import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ActiveLearningPipeline:
    def __init__(self, db_path: str = "smarfa.db", retraining_dir: str = "data_retraining"):
        self.db_path = db_path
        self.retraining_dir = retraining_dir
        os.makedirs(self.retraining_dir, exist_ok=True)
        self._init_database()

    def _init_database(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS hard_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_path TEXT NOT NULL,
                    crop_predicted TEXT NOT NULL,
                    disease_predicted TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    verified INTEGER DEFAULT 0,
                    crop_verified TEXT,
                    disease_verified TEXT
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"[ActiveLearning] Failed to initialize SQLite AL index: {e}")

    def log_hard_sample(self, src_img_path: str, crop_predicted: str, disease_predicted: str, conf: float):
        """Saves a copy of low-confidence predictions to the hard sample retraining stack."""
        try:
            if not os.path.exists(src_img_path):
                return
            filename = os.path.basename(src_img_path)
            dest_path = os.path.join(self.retraining_dir, filename)
            shutil.copy(src_img_path, dest_path)
            
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO hard_samples (image_path, crop_predicted, disease_predicted, confidence, timestamp, verified) VALUES (?, ?, ?, ?, ?, 0)",
                (dest_path, crop_predicted, disease_predicted, conf, datetime.utcnow().isoformat())
            )
            conn.commit()
            conn.close()
            logger.info(f"[ActiveLearning] Mined hard sample: {filename} (Confidence: {conf:.2f})")
        except Exception as e:
            logger.warning(f"[ActiveLearning] Hard sample mining error: {e}")

    def submit_expert_label(self, sample_id: int, correct_crop: str, correct_disease: str):
        """Routes agronomist corrected label to target training directories."""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("SELECT image_path FROM hard_samples WHERE id = ?", (sample_id,))
            row = cur.fetchone()
            if not row:
                conn.close()
                return
            img_path = row[0]
            
            cur.execute(
                "UPDATE hard_samples SET crop_verified = ?, disease_verified = ?, verified = 1 WHERE id = ?",
                (correct_crop, correct_disease, sample_id)
            )
            
            if os.path.exists(img_path):
                target_dir = os.path.join(self.retraining_dir, f"{correct_crop}___{correct_disease}")
                os.makedirs(target_dir, exist_ok=True)
                shutil.move(img_path, os.path.join(target_dir, os.path.basename(img_path)))
                
            conn.commit()
            conn.close()
            logger.info(f"[ActiveLearning] Hard sample #{sample_id} verified as: {correct_crop} ({correct_disease})")
        except Exception as e:
            logger.error(f"[ActiveLearning] Error logging expert feedback: {e}")
            
    def fetch_unverified_samples(self) -> list:
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("SELECT * FROM hard_samples WHERE verified = 0")
            rows = cur.fetchall()
            conn.close()
            return [dict(zip(["id", "image_path", "crop_predicted", "disease_predicted", "confidence", "timestamp", "verified", "crop_verified", "disease_verified"], r)) for r in rows]
        except Exception:
            return []
