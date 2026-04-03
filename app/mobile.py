from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

# In-memory registry (for demo). Replace with a DB collection in production.
_device_tokens: Dict[str, str] = {}

class DeviceRegistration:
    def __init__(self, farmer_id: str, token: str):
        self.farmer_id = farmer_id
        self.token = token


def register_device(farmer_id: str, token: str):
    _device_tokens[farmer_id] = token
    logger.info("Registered device for farmer %s, token=%s", farmer_id, token)
    return {"farmer_id": farmer_id, "token": token, "status": "registered"}


def list_devices() -> List[Dict[str, str]]:
    return [{"farmer_id": fid, "token": tok} for fid, tok in _device_tokens.items()]


def send_push(farmer_id: str, title: str, body: str):
    # Placeholder: integrate with FCM/APNs here.
    token = _device_tokens.get(farmer_id)
    if not token:
        raise ValueError(f"No device registered for farmer {farmer_id}")

    logger.info("Push to %s (%s): %s - %s", farmer_id, token, title, body)
    return {"farmer_id": farmer_id, "title": title, "body": body, "sent": True}
