from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class CropData(Base):
    __tablename__ = "crop_data"
    id = Column(Integer, primary_key=True, autoincrement=True)
    crop_id = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    height_cm = Column(Float, nullable=False)
    soil_moisture = Column(Float, nullable=False)
    temperature_c = Column(Float, nullable=False)

class IntrusionEvent(Base):
    __tablename__ = "intrusion_event"
    id = Column(Integer, primary_key=True, autoincrement=True)
    crop_id = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    motion_detected = Column(Boolean, nullable=False)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    crop_id = Column(String, nullable=False)
    type = Column(String, nullable=False)
    message = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
