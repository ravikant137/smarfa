from datetime import datetime, timedelta

from app.alerts import track_alert
from app.config import settings

AUTO_IRRIGATION_THRESHOLD = 30   # Soil moisture % below which pump auto-starts
AUTO_IRRIGATION_DURATION = 120   # seconds

def _auto_start_pump(db, crop_id: str, moisture: float, reason: str):
    """Auto-activate the water pump when soil moisture is critically low."""
    row = db.execute(
        "SELECT id FROM water_pump_log WHERE crop_id=? AND status='running' LIMIT 1",
        (crop_id,)
    ).fetchone()
    if row:
        return  # pump already running
    now = datetime.utcnow().isoformat()
    db.execute(
        "INSERT INTO water_pump_log (crop_id,timestamp,trigger_type,reason,moisture_before,duration_seconds,status) VALUES (?,?,?,?,?,?,?)",
        (crop_id, now, "auto", reason, moisture, AUTO_IRRIGATION_DURATION, "running")
    )
    db.commit()
    track_alert(crop_id, "pump_auto_start",
        f"💧 Water pump AUTO-STARTED — soil moisture at {moisture:.1f}% (below {AUTO_IRRIGATION_THRESHOLD}%). "
        f"Irrigating for {AUTO_IRRIGATION_DURATION}s. Reason: {reason}",
        db)

def process_growth_reading(db, record):
    window = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    rows = db.execute(
        "SELECT height_cm, soil_moisture, temperature_c, timestamp FROM crop_data WHERE crop_id=? AND timestamp>=? ORDER BY timestamp DESC",
        (record.crop_id, window)
    ).fetchall()
    if len(rows) < 2:
        return

    latest_h = rows[0]["height_cm"]
    previous_h = rows[1]["height_cm"]
    growth = latest_h - previous_h

    if growth < 0:
        track_alert(record.crop_id, "growth_drop", f"Height decreased from {previous_h:.2f} cm to {latest_h:.2f} cm. Solution: Check for pest damage or nutrient deficiencies. Apply balanced fertilizer and inspect for root rot.", db)

    elif growth < settings.growth_rate_min:
        track_alert(record.crop_id, "growth_slow", f"Low growth rate {growth:.3f} cm over last period; check irrigation/nutrition. Solution: Increase watering frequency and test soil pH. Consider foliar feeding with micronutrients.", db)

    if not (15 <= record.temperature_c <= 35):
        if record.temperature_c < 15:
            track_alert(record.crop_id, "temp_warning", f"Temperature at {record.temperature_c:.1f}°C - too cold for optimal growth. Solution: Install row covers or use thermal blankets to protect crops from frost damage.", db)
        else:
            track_alert(record.crop_id, "temp_warning", f"Temperature at {record.temperature_c:.1f}°C - too hot, risking heat stress. Solution: Provide shade cloth and increase irrigation to cool soil and prevent wilting.", db)

    if not (30 <= record.soil_moisture <= 70):
        if record.soil_moisture < 30:
            track_alert(record.crop_id, "moisture_warning", f"Soil moisture at {record.soil_moisture:.1f}% - critically low. Solution: Irrigate immediately with drip system to reach 40-60% for healthy root development and prevent yield loss.", db)
            _auto_start_pump(db, record.crop_id, record.soil_moisture,
                f"Soil moisture critically low at {record.soil_moisture:.1f}%")
        else:
            track_alert(record.crop_id, "moisture_warning", f"Soil moisture at {record.soil_moisture:.1f}% - too high, risking root rot. Solution: Improve drainage by adding organic matter and reduce watering frequency.", db)


def process_intrusion_reading(db, event):
    if event.motion_detected:
        track_alert(event.crop_id, "intrusion_alarm", "Motion detected on land; possible intrusion. Solution: Check perimeter fencing and install motion-activated lights to deter wildlife. Consider electric fencing for persistent issues.", db)
