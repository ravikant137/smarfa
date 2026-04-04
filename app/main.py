from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path
import bcrypt

from app.database import init_db, get_session
from app.models import CropData, IntrusionEvent, Alert, User, WaterPumpLog
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


@app.post("/analyze_crop")
async def analyze_crop(payload: CropImagePayload):
    if not payload.image_base64:
        raise HTTPException(status_code=400, detail="No image provided")
    result = await analyze_crop_image(payload.image_base64)
    return result


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


# ── Detailed Farm Reports ─────────────────────────────────────────────────
@app.get("/reports/overview")
async def reports_overview():
    from sqlalchemy import func
    session = get_session()
    from datetime import timedelta
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    # Sensor stats
    recent_data = session.query(CropData).filter(CropData.timestamp >= week_ago).all()
    total_alerts = session.query(Alert).filter(Alert.timestamp >= week_ago).count()
    total_alerts_all = session.query(Alert).count()
    pump_activations = session.query(WaterPumpLog).filter(WaterPumpLog.timestamp >= week_ago).count()

    if recent_data:
        avg_temp = round(sum(r.temperature_c for r in recent_data) / len(recent_data), 1)
        avg_moisture = round(sum(r.soil_moisture for r in recent_data) / len(recent_data), 1)
        avg_height = round(sum(r.height_cm for r in recent_data) / len(recent_data), 1)
        min_moisture = round(min(r.soil_moisture for r in recent_data), 1)
        max_temp = round(max(r.temperature_c for r in recent_data), 1)
        min_temp = round(min(r.temperature_c for r in recent_data), 1)
        crops = list(set(r.crop_id for r in recent_data))
    else:
        avg_temp = avg_moisture = avg_height = min_moisture = max_temp = min_temp = 0.0
        crops = []

    # Alert breakdown
    alert_types = {}
    alerts_week = session.query(Alert).filter(Alert.timestamp >= week_ago).all()
    for a in alerts_week:
        alert_types[a.type] = alert_types.get(a.type, 0) + 1

    # Growth trend (last 7 days by day)
    daily_data = {}
    for r in recent_data:
        day = r.timestamp.strftime("%Y-%m-%d")
        if day not in daily_data:
            daily_data[day] = {"heights": [], "moistures": [], "temps": []}
        daily_data[day]["heights"].append(r.height_cm)
        daily_data[day]["moistures"].append(r.soil_moisture)
        daily_data[day]["temps"].append(r.temperature_c)

    trends = []
    for day in sorted(daily_data.keys()):
        d = daily_data[day]
        trends.append({
            "date": day,
            "avg_height": round(sum(d["heights"]) / len(d["heights"]), 1),
            "avg_moisture": round(sum(d["moistures"]) / len(d["moistures"]), 1),
            "avg_temp": round(sum(d["temps"]) / len(d["temps"]), 1),
        })

    # Health score (0-100)
    health_score = 85
    if avg_moisture < 30:
        health_score -= 25
    elif avg_moisture < 40:
        health_score -= 10
    if avg_temp > 38 or avg_temp < 10:
        health_score -= 15
    if total_alerts > 10:
        health_score -= 20
    elif total_alerts > 5:
        health_score -= 10
    health_score = max(0, min(100, health_score))

    return {
        "health_score": health_score,
        "total_crops": len(crops),
        "crops": crops,
        "week_summary": {
            "avg_temp": avg_temp, "min_temp": min_temp, "max_temp": max_temp,
            "avg_moisture": avg_moisture, "min_moisture": min_moisture,
            "avg_height": avg_height,
            "alerts_count": total_alerts,
            "alerts_total": total_alerts_all,
            "pump_activations": pump_activations,
            "readings_count": len(recent_data),
        },
        "alert_breakdown": alert_types,
        "daily_trends": trends,
    }


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

