from datetime import datetime, timedelta
from sqlalchemy import func

from app.models import CropData, IntrusionEvent
from app.alerts import track_alert
from app.config import settings

def process_growth_reading(session, record: CropData):
    window = datetime.utcnow() - timedelta(hours=24)
    history = session.query(CropData).filter(CropData.crop_id == record.crop_id, CropData.timestamp >= window).order_by(CropData.timestamp.desc()).all()
    if len(history) < 2:
        return

    latest = history[0]
    previous = history[1]
    growth = latest.height_cm - previous.height_cm

    if growth < 0:
        track_alert(record.crop_id, "growth_drop", f"Height decreased from {previous.height_cm:.2f} cm to {latest.height_cm:.2f} cm. Solution: Check for pest damage or nutrient deficiencies. Apply balanced fertilizer and inspect for root rot.", session)

    elif growth < settings.growth_rate_min:
        track_alert(record.crop_id, "growth_slow", f"Low growth rate {growth:.3f} cm over last period; check irrigation/nutrition. Solution: Increase watering frequency and test soil pH. Consider foliar feeding with micronutrients.", session)

    if not (15 <= record.temperature_c <= 35):
        if record.temperature_c < 15:
            track_alert(record.crop_id, "temp_warning", f"Temperature at {record.temperature_c:.1f}°C - too cold for optimal growth. Solution: Install row covers or use thermal blankets to protect crops from frost damage.", session)
        else:
            track_alert(record.crop_id, "temp_warning", f"Temperature at {record.temperature_c:.1f}°C - too hot, risking heat stress. Solution: Provide shade cloth and increase irrigation to cool soil and prevent wilting.", session)

    if not (30 <= record.soil_moisture <= 70):
        if record.soil_moisture < 30:
            track_alert(record.crop_id, "moisture_warning", f"Soil moisture at {record.soil_moisture:.1f}% - critically low. Solution: Irrigate immediately with drip system to reach 40-60% for healthy root development and prevent yield loss.", session)
        else:
            track_alert(record.crop_id, "moisture_warning", f"Soil moisture at {record.soil_moisture:.1f}% - too high, risking root rot. Solution: Improve drainage by adding organic matter and reduce watering frequency.", session)


def process_intrusion_reading(session, event: IntrusionEvent):
    if event.motion_detected:
        track_alert(event.crop_id, "intrusion_alarm", "Motion detected on land; possible intrusion. Solution: Check perimeter fencing and install motion-activated lights to deter wildlife. Consider electric fencing for persistent issues.", session)
