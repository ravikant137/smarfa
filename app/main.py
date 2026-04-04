from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path
import bcrypt

from app.database import init_db, get_session
from app.models import CropData, IntrusionEvent, Alert, User, WaterPumpLog, ScanHistory
from app.sensors import process_growth_reading, process_intrusion_reading
from app.config import settings
from app.mobile import register_device, list_devices, send_push
from app.crop_ai import analyze_crop_image


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

app = FastAPI(title="Smart AI Farming")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

@app.on_event("startup")
async def startup_event():
    init_db()

class SensorPayload(BaseModel):
    crop_id: str
    type: str
    timestamp: datetime | None = None
    height_cm: float | None = None
    soil_moisture: float | None = None
    temperature_c: float | None = None
    motion: bool | None = None

@app.post("/sensor_data")
async def ingest_sensor_data(payload: SensorPayload):
    ts = payload.timestamp or datetime.utcnow()
    session = get_session()

    if payload.type == "growth":
        if payload.height_cm is None or payload.soil_moisture is None or payload.temperature_c is None:
            raise HTTPException(status_code=400, detail="Missing fields for growth record")
        record = CropData(
            crop_id=payload.crop_id,
            timestamp=ts,
            height_cm=payload.height_cm,
            soil_moisture=payload.soil_moisture,
            temperature_c=payload.temperature_c,
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        process_growth_reading(session, record)
        return {"status": "growth data recorded", "id": record.id}

    if payload.type == "intrusion":
        if payload.motion is None:
            raise HTTPException(status_code=400, detail="Missing motion field for intrusion record")
        record = IntrusionEvent(
            crop_id=payload.crop_id,
            timestamp=ts,
            motion_detected=payload.motion,
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        process_intrusion_reading(session, record)
        return {"status": "intrusion data recorded", "id": record.id}

    raise HTTPException(status_code=400, detail="Unknown sensor type")

class MobileRegister(BaseModel):
    farmer_id: str
    device_token: str

class MobilePush(BaseModel):
    farmer_id: str
    title: str
    body: str

class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

@app.post("/register")
async def register_user(payload: UserRegister):
    session = get_session()
    existing = session.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    hashed = hash_password(payload.password)
    user = User(username=payload.username, password_hash=hashed)
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"status": "user registered", "id": user.id}

@app.post("/login")
async def login_user(payload: UserLogin):
    session = get_session()
    user = session.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"status": "login successful", "user_id": user.id}

@app.get("/alerts")
async def list_alerts():
    session = get_session()
    return session.query(Alert).order_by(Alert.timestamp.desc()).limit(50).all()

@app.post("/mobile/register")
async def mobile_register(payload: MobileRegister):
    return register_device(payload.farmer_id, payload.device_token)

@app.get("/mobile/devices")
async def mobile_devices():
    return list_devices()

@app.post("/mobile/send_push")
async def mobile_send_push(payload: MobilePush):
    try:
        return send_push(payload.farmer_id, payload.title, payload.body)
    except Exception as ex:
        raise HTTPException(status_code=404, detail=str(ex))


class CropImagePayload(BaseModel):
    image_base64: str
    crop_hint: str | None = None


@app.post("/analyze_crop")
async def analyze_crop(payload: CropImagePayload):
    if not payload.image_base64:
        raise HTTPException(status_code=400, detail="No image provided")
    session = get_session()
    result = await analyze_crop_image(payload.image_base64, crop_hint=payload.crop_hint or None)

    now = datetime.utcnow()
    severity = str(result.get("severity") or "warning")
    crop_name = str(result.get("crop_detected") or "General Crop")
    health_txt = str(result.get("health_assessment") or "")
    confidence = float(result.get("ai_confidence") or 95.0)

    scan = ScanHistory(
        timestamp=now,
        crop_detected=crop_name,
        severity=severity,
        ai_confidence=confidence,
        health_assessment=health_txt,
        model_used=str(result.get("_model") or "unknown"),
    )
    session.add(scan)

    # Create an alert for every crop scan so it shows on Alerts screen
    alert_type = f"crop_{severity}"
    snippet = health_txt[:220] if health_txt else f"{crop_name} requires attention."
    alert_msg = f"[Crop Scan] {crop_name} — {severity.upper()} | Confidence: {confidence:.0f}%. {snippet}"
    alert = Alert(
        crop_id="crop_scan",
        type=alert_type,
        message=alert_msg,
        timestamp=now,
    )
    session.add(alert)
    session.commit()
    return result


@app.get("/scan_history")
async def scan_history(limit: int = 20):
    session = get_session()
    bounded = max(1, min(limit, 100))
    rows = session.query(ScanHistory).order_by(ScanHistory.timestamp.desc()).limit(bounded).all()
    return [
        {
            "id": r.id,
            "timestamp": str(r.timestamp),
            "crop_detected": r.crop_detected,
            "severity": r.severity,
            "ai_confidence": round(float(r.ai_confidence), 1),
            "health_assessment": r.health_assessment,
            "model_used": r.model_used,
        }
        for r in rows
    ]


@app.get("/reports/overview")
async def reports_overview():
    from datetime import timedelta
    session = get_session()
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    # Scan history
    all_scans = session.query(ScanHistory).order_by(ScanHistory.timestamp.desc()).all()
    recent_scans = [s for s in all_scans if s.timestamp >= week_ago]

    unique_crops = len(set(s.crop_detected for s in all_scans))
    avg_conf = 0.0
    if recent_scans:
        avg_conf = sum(s.ai_confidence for s in recent_scans) / len(recent_scans)
        healthy_count = sum(1 for s in recent_scans if s.severity == "healthy")
        health_score = int((healthy_count / len(recent_scans)) * 100)
    else:
        health_score = 0

    # Alerts
    recent_alerts = session.query(Alert).filter(Alert.timestamp >= week_ago).all()
    total_alerts_all = session.query(Alert).count()
    breakdown: dict = {}
    for a in recent_alerts:
        breakdown[a.type] = breakdown.get(a.type, 0) + 1

    # Sensor data
    sensor_data = session.query(CropData).filter(CropData.timestamp >= week_ago).all()
    avg_temp = round(sum(s.temperature_c for s in sensor_data) / len(sensor_data), 1) if sensor_data else 0
    avg_moisture = round(sum(s.soil_moisture for s in sensor_data) / len(sensor_data), 1) if sensor_data else 0
    min_temp = round(min((s.temperature_c for s in sensor_data), default=0), 1)
    max_temp = round(max((s.temperature_c for s in sensor_data), default=0), 1)
    min_moisture = round(min((s.soil_moisture for s in sensor_data), default=0), 1)
    avg_height = round(sum(s.height_cm for s in sensor_data) / len(sensor_data), 1) if sensor_data else 0
    pump_count = session.query(WaterPumpLog).filter(WaterPumpLog.timestamp >= week_ago).count()

    # Daily trends
    daily_data: dict = {}
    for r in sensor_data:
        day = r.timestamp.strftime("%Y-%m-%d")
        if day not in daily_data:
            daily_data[day] = {"heights": [], "moistures": [], "temps": []}
        daily_data[day]["heights"].append(r.height_cm)
        daily_data[day]["moistures"].append(r.soil_moisture)
        daily_data[day]["temps"].append(r.temperature_c)
    trends = []
    for day in sorted(daily_data.keys()):
        dd = daily_data[day]
        trends.append({
            "date": day,
            "avg_height": round(sum(dd["heights"]) / len(dd["heights"]), 1),
            "avg_moisture": round(sum(dd["moistures"]) / len(dd["moistures"]), 1),
            "avg_temp": round(sum(dd["temps"]) / len(dd["temps"]), 1),
        })

    return {
        "health_score": health_score,
        "total_crops": unique_crops,
        "total_scans": len(all_scans),
        "avg_confidence": round(avg_conf, 1),
        "recent_scans": [
            {
                "id": s.id,
                "timestamp": str(s.timestamp),
                "crop_detected": s.crop_detected,
                "severity": s.severity,
                "ai_confidence": round(float(s.ai_confidence), 1),
                "health_assessment": s.health_assessment[:120] if s.health_assessment else "",
            }
            for s in all_scans[:10]
        ],
        "week_summary": {
            "alerts_count": len(recent_alerts),
            "alerts_total": total_alerts_all,
            "avg_temp": avg_temp,
            "avg_moisture": avg_moisture,
            "min_temp": min_temp,
            "max_temp": max_temp,
            "min_moisture": min_moisture,
            "avg_height": avg_height,
            "readings_count": len(sensor_data),
            "pump_activations": pump_count,
            "scan_count": len(recent_scans),
            "avg_confidence": round(avg_conf, 1),
        },
        "alert_breakdown": breakdown,
        "daily_trends": trends,
    }


# ── Water Pump Control ────────────────────────────────────────────────────
class PumpAction(BaseModel):
    crop_id: str
    duration_seconds: int = 120

@app.post("/pump/start")
async def start_pump(payload: PumpAction):
    session = get_session()
    latest = session.query(CropData).filter(
        CropData.crop_id == payload.crop_id
    ).order_by(CropData.timestamp.desc()).first()
    moisture = latest.soil_moisture if latest else None
    log = WaterPumpLog(
        crop_id=payload.crop_id,
        timestamp=datetime.utcnow(),
        trigger="manual",
        reason="Manual activation by farmer",
        moisture_before=moisture,
        duration_seconds=payload.duration_seconds,
        status="running",
    )
    session.add(log)
    session.commit()
    session.refresh(log)
    return {"status": "pump_started", "id": log.id, "duration": payload.duration_seconds, "moisture_before": moisture}

@app.post("/pump/stop")
async def stop_pump(payload: PumpAction):
    session = get_session()
    running = session.query(WaterPumpLog).filter(
        WaterPumpLog.crop_id == payload.crop_id,
        WaterPumpLog.status == "running"
    ).order_by(WaterPumpLog.timestamp.desc()).first()
    if running:
        running.status = "stopped"
        session.commit()
    return {"status": "pump_stopped", "crop_id": payload.crop_id}

@app.get("/pump/status/{crop_id}")
async def pump_status(crop_id: str):
    session = get_session()
    running = session.query(WaterPumpLog).filter(
        WaterPumpLog.crop_id == crop_id,
        WaterPumpLog.status == "running"
    ).first()
    logs = session.query(WaterPumpLog).filter(
        WaterPumpLog.crop_id == crop_id
    ).order_by(WaterPumpLog.timestamp.desc()).limit(10).all()
    return {
        "is_running": running is not None,
        "current": {"id": running.id, "started": str(running.timestamp), "duration": running.duration_seconds, "reason": running.reason} if running else None,
        "recent_logs": [{"id": l.id, "timestamp": str(l.timestamp), "trigger": l.trigger, "reason": l.reason, "moisture_before": l.moisture_before, "duration": l.duration_seconds, "status": l.status} for l in logs]
    }

@app.get("/pump/logs")
async def pump_logs():
    session = get_session()
    logs = session.query(WaterPumpLog).order_by(WaterPumpLog.timestamp.desc()).limit(50).all()
    return [{"id": l.id, "crop_id": l.crop_id, "timestamp": str(l.timestamp), "trigger": l.trigger, "reason": l.reason, "moisture_before": l.moisture_before, "duration": l.duration_seconds, "status": l.status} for l in logs]


# ── Ollama status endpoint ────────────────────────────────────────────────
@app.get("/ai_status")
async def ai_status():
    import httpx
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get("http://localhost:11434/api/tags")
            r.raise_for_status()
            models = [m["name"] for m in r.json().get("models", [])]
            has_vision = any(m for m in models if "llava" in m or "moondream" in m)
            return {"ollama": True, "models": models, "vision_ready": has_vision}
    except Exception:
        return {"ollama": False, "models": [], "vision_ready": False}


# ── Serve web frontend ───────────────────────────────────────────────────
@app.get("/")
async def serve_index():
    return FileResponse(
        WEB_DIR / "index.html",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"}
    )


# Mount static assets AFTER API routes so /api paths aren't shadowed
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

