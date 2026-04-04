from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from passlib.context import CryptContext

from app.database import init_db, get_session
from app.models import CropData, IntrusionEvent, Alert, User
from app.sensors import process_growth_reading, process_intrusion_reading
from app.config import settings
from app.mobile import register_device, list_devices, send_push

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(title="Smart AI Farming")

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
    hashed = pwd_context.hash(payload.password)
    user = User(username=payload.username, password_hash=hashed)
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"status": "user registered", "id": user.id}

@app.post("/login")
async def login_user(payload: UserLogin):
    session = get_session()
    user = session.query(User).filter(User.username == payload.username).first()
    if not user or not pwd_context.verify(payload.password, user.password_hash):
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

