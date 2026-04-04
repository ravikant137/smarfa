"""
Lightweight data helpers — no SQLAlchemy needed.
All persistence is done via sqlite3 in database.py.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class CropData:
    crop_id: str
    timestamp: datetime
    height_cm: float
    soil_moisture: float
    temperature_c: float
    id: Optional[int] = None


@dataclass
class IntrusionEvent:
    crop_id: str
    timestamp: datetime
    motion_detected: bool
    id: Optional[int] = None


@dataclass
class Alert:
    crop_id: str
    type: str
    message: str
    timestamp: datetime
    id: Optional[int] = None


@dataclass
class User:
    username: str
    password_hash: str
    id: Optional[int] = None


@dataclass
class WaterPumpLog:
    crop_id: str
    timestamp: datetime
    trigger: str
    reason: str
    duration_seconds: int
    status: str
    moisture_before: Optional[float] = None
    id: Optional[int] = None


@dataclass
class ScanHistory:
    timestamp: datetime
    crop_detected: str
    severity: str
    ai_confidence: float
    health_assessment: str
    model_used: Optional[str] = None
    id: Optional[int] = None
