from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
from pathlib import Path
import bcrypt

from app.database import init_db, get_db
from app.models import CropData, IntrusionEvent
from app.sensors import process_growth_reading, process_intrusion_reading
from app.config import settings
from app.mobile import register_device, list_devices, send_push
from app.crop_ai import analyze_crop_image, CROP_LIFECYCLE, TREATMENT_DB


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
    ts = (payload.timestamp or datetime.utcnow()).isoformat()
    db = get_db()

    if payload.type == "growth":
        if payload.height_cm is None or payload.soil_moisture is None or payload.temperature_c is None:
            raise HTTPException(status_code=400, detail="Missing fields for growth record")
        cur = db.execute(
            "INSERT INTO crop_data (crop_id,timestamp,height_cm,soil_moisture,temperature_c) VALUES (?,?,?,?,?)",
            (payload.crop_id, ts, payload.height_cm, payload.soil_moisture, payload.temperature_c)
        )
        db.commit()
        record = CropData(crop_id=payload.crop_id, timestamp=payload.timestamp or datetime.utcnow(),
                          height_cm=payload.height_cm, soil_moisture=payload.soil_moisture,
                          temperature_c=payload.temperature_c, id=cur.lastrowid)
        process_growth_reading(db, record)
        return {"status": "growth data recorded", "id": cur.lastrowid}

    if payload.type == "intrusion":
        if payload.motion is None:
            raise HTTPException(status_code=400, detail="Missing motion field for intrusion record")
        cur = db.execute(
            "INSERT INTO intrusion_event (crop_id,timestamp,motion_detected) VALUES (?,?,?)",
            (payload.crop_id, ts, int(payload.motion))
        )
        db.commit()
        event = IntrusionEvent(crop_id=payload.crop_id, timestamp=payload.timestamp or datetime.utcnow(),
                               motion_detected=payload.motion, id=cur.lastrowid)
        process_intrusion_reading(db, event)
        return {"status": "intrusion data recorded", "id": cur.lastrowid}

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
    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE username=?", (payload.username,)).fetchone()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    hashed = hash_password(payload.password)
    cur = db.execute("INSERT INTO users (username, password_hash) VALUES (?,?)", (payload.username, hashed))
    db.commit()
    return {"status": "user registered", "id": cur.lastrowid}

@app.post("/login")
async def login_user(payload: UserLogin):
    db = get_db()
    user = db.execute("SELECT id, password_hash FROM users WHERE username=?", (payload.username,)).fetchone()
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"status": "login successful", "user_id": user["id"]}

@app.get("/alerts")
async def list_alerts():
    db = get_db()
    rows = db.execute("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 50").fetchall()
    return [dict(r) for r in rows]

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
    db = get_db()
    result = await analyze_crop_image(payload.image_base64, crop_hint=payload.crop_hint or None)

    now = datetime.utcnow().isoformat()
    severity = str(result.get("severity") or "warning")
    crop_name = str(result.get("crop_detected") or "General Crop")
    health_txt = str(result.get("health_assessment") or "")
    confidence = float(result.get("ai_confidence") or 95.0)
    model_used = str(result.get("_model") or "unknown")

    db.execute(
        "INSERT INTO scan_history (timestamp,crop_detected,severity,ai_confidence,health_assessment,model_used) VALUES (?,?,?,?,?,?)",
        (now, crop_name, severity, confidence, health_txt, model_used)
    )

    snippet = health_txt[:220] if health_txt else f"{crop_name} requires attention."
    alert_msg = f"[Crop Scan] {crop_name} — {severity.upper()} | Confidence: {confidence:.0f}%. {snippet}"
    db.execute(
        "INSERT INTO alerts (crop_id, type, message, timestamp) VALUES (?,?,?,?)",
        ("crop_scan", f"crop_{severity}", alert_msg, now)
    )
    db.commit()
    return result


@app.post("/analyze_structured")
async def analyze_structured(payload: CropImagePayload):
    """Return the full structured JSON (crop_identification, disease, treatment, lifecycle)."""
    if not payload.image_base64:
        raise HTTPException(status_code=400, detail="No image provided")
    result = await analyze_crop_image(payload.image_base64, crop_hint=payload.crop_hint or None)
    structured = result.get("structured", {})
    return structured


@app.get("/crop_lifecycle/{crop_name}")
async def get_crop_lifecycle(crop_name: str):
    """Return lifecycle data for a specific crop."""
    key = crop_name.strip().title()
    lc = CROP_LIFECYCLE.get(key)
    if not lc:
        # Try case-insensitive
        for k, v in CROP_LIFECYCLE.items():
            if k.lower() == crop_name.lower():
                lc = v
                break
    if not lc:
        raise HTTPException(status_code=404, detail=f"Lifecycle data not available for '{crop_name}'. Supported: {', '.join(CROP_LIFECYCLE.keys())}")
    return lc


@app.get("/crop_lifecycle")
async def list_crop_lifecycles():
    """Return lifecycle data for all supported crops."""
    return {name: data for name, data in CROP_LIFECYCLE.items()}


@app.get("/treatments")
async def list_treatments():
    """Return all available treatment data."""
    return TREATMENT_DB


@app.get("/scan_history")
async def scan_history(limit: int = 20):
    db = get_db()
    bounded = max(1, min(limit, 100))
    rows = db.execute("SELECT * FROM scan_history ORDER BY timestamp DESC LIMIT ?", (bounded,)).fetchall()
    return [
        {
            "id": r["id"],
            "timestamp": r["timestamp"],
            "crop_detected": r["crop_detected"],
            "severity": r["severity"],
            "ai_confidence": round(float(r["ai_confidence"]), 1),
            "health_assessment": r["health_assessment"],
            "model_used": r["model_used"],
        }
        for r in rows
    ]


@app.get("/reports/overview")
async def reports_overview():
    db = get_db()
    now = datetime.utcnow()
    week_ago = (now - timedelta(days=7)).isoformat()

    all_scans = db.execute("SELECT * FROM scan_history ORDER BY timestamp DESC").fetchall()
    recent_scans = [s for s in all_scans if s["timestamp"] >= week_ago]

    unique_crops = len(set(s["crop_detected"] for s in all_scans))
    avg_conf = 0.0
    if recent_scans:
        avg_conf = sum(s["ai_confidence"] for s in recent_scans) / len(recent_scans)
        healthy_count = sum(1 for s in recent_scans if s["severity"] == "healthy")
        health_score = int((healthy_count / len(recent_scans)) * 100)
    else:
        health_score = 0

    recent_alerts = db.execute("SELECT * FROM alerts WHERE timestamp >= ?", (week_ago,)).fetchall()
    total_alerts_all = db.execute("SELECT COUNT(*) as c FROM alerts").fetchone()["c"]
    breakdown: dict = {}
    for a in recent_alerts:
        breakdown[a["type"]] = breakdown.get(a["type"], 0) + 1

    sensor_data = db.execute("SELECT * FROM crop_data WHERE timestamp >= ?", (week_ago,)).fetchall()
    avg_temp = round(sum(s["temperature_c"] for s in sensor_data) / len(sensor_data), 1) if sensor_data else 0
    avg_moisture = round(sum(s["soil_moisture"] for s in sensor_data) / len(sensor_data), 1) if sensor_data else 0
    min_temp = round(min((s["temperature_c"] for s in sensor_data), default=0), 1)
    max_temp = round(max((s["temperature_c"] for s in sensor_data), default=0), 1)
    min_moisture = round(min((s["soil_moisture"] for s in sensor_data), default=0), 1)
    avg_height = round(sum(s["height_cm"] for s in sensor_data) / len(sensor_data), 1) if sensor_data else 0
    pump_count = db.execute("SELECT COUNT(*) as c FROM water_pump_log WHERE timestamp >= ?", (week_ago,)).fetchone()["c"]

    daily_data: dict = {}
    for r in sensor_data:
        day = r["timestamp"][:10]
        if day not in daily_data:
            daily_data[day] = {"heights": [], "moistures": [], "temps": []}
        daily_data[day]["heights"].append(r["height_cm"])
        daily_data[day]["moistures"].append(r["soil_moisture"])
        daily_data[day]["temps"].append(r["temperature_c"])
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
                "id": s["id"],
                "timestamp": s["timestamp"],
                "crop_detected": s["crop_detected"],
                "severity": s["severity"],
                "ai_confidence": round(float(s["ai_confidence"]), 1),
                "health_assessment": (s["health_assessment"] or "")[:120],
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
    db = get_db()
    latest = db.execute(
        "SELECT soil_moisture FROM crop_data WHERE crop_id=? ORDER BY timestamp DESC LIMIT 1",
        (payload.crop_id,)
    ).fetchone()
    moisture = latest["soil_moisture"] if latest else None
    now = datetime.utcnow().isoformat()
    cur = db.execute(
        "INSERT INTO water_pump_log (crop_id,timestamp,trigger_type,reason,moisture_before,duration_seconds,status) VALUES (?,?,?,?,?,?,?)",
        (payload.crop_id, now, "manual", "Manual activation by farmer", moisture, payload.duration_seconds, "running")
    )
    db.commit()
    return {"status": "pump_started", "id": cur.lastrowid, "duration": payload.duration_seconds, "moisture_before": moisture}

@app.post("/pump/stop")
async def stop_pump(payload: PumpAction):
    db = get_db()
    running = db.execute(
        "SELECT id FROM water_pump_log WHERE crop_id=? AND status='running' ORDER BY timestamp DESC LIMIT 1",
        (payload.crop_id,)
    ).fetchone()
    if running:
        db.execute("UPDATE water_pump_log SET status='stopped' WHERE id=?", (running["id"],))
        db.commit()
    return {"status": "pump_stopped", "crop_id": payload.crop_id}

@app.get("/pump/status/{crop_id}")
async def pump_status(crop_id: str):
    db = get_db()
    running = db.execute(
        "SELECT id, timestamp, duration_seconds, reason FROM water_pump_log WHERE crop_id=? AND status='running' LIMIT 1",
        (crop_id,)
    ).fetchone()
    logs = db.execute(
        "SELECT * FROM water_pump_log WHERE crop_id=? ORDER BY timestamp DESC LIMIT 10",
        (crop_id,)
    ).fetchall()
    return {
        "is_running": running is not None,
        "current": {"id": running["id"], "started": running["timestamp"], "duration": running["duration_seconds"], "reason": running["reason"]} if running else None,
        "recent_logs": [{"id": l["id"], "timestamp": l["timestamp"], "trigger": l["trigger_type"], "reason": l["reason"], "moisture_before": l["moisture_before"], "duration": l["duration_seconds"], "status": l["status"]} for l in logs]
    }

@app.get("/pump/logs")
async def pump_logs():
    db = get_db()
    logs = db.execute("SELECT * FROM water_pump_log ORDER BY timestamp DESC LIMIT 50").fetchall()
    return [{"id": l["id"], "crop_id": l["crop_id"], "timestamp": l["timestamp"], "trigger": l["trigger_type"], "reason": l["reason"], "moisture_before": l["moisture_before"], "duration": l["duration_seconds"], "status": l["status"]} for l in logs]


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

