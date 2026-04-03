import logging
from datetime import datetime

from app.config import settings
from app.mobile import list_devices, send_push

logger = logging.getLogger(__name__)

# Placeholder for Twilio SMS or other push provider.
# For production, fill with proper SDK and credentials.

def send_sms(to_number: str, message: str):
    logger.info("SMS to %s: %s", to_number, message)
    # Example Twilio block (commented):
    # from twilio.rest import Client
    # client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    # client.messages.create(body=message, from_=settings.twilio_from_number, to=to_number)

def notify_farmers(message: str):
    for msisdn in settings.farmer_phone_numbers:
        send_sms(msisdn, message)

    # Mobile push too
    for dev in list_devices():
        try:
            send_push(dev["farmer_id"], "SmartFarm Alert", message)
        except Exception as ex:
            logger.warning("Failed mobile push to %s: %s", dev["farmer_id"], ex)


def track_alert(crop_id: str, alert_type: str, message: str, session):
    from app.models import Alert
    alert = Alert(crop_id=crop_id, type=alert_type, message=message, timestamp=datetime.utcnow())
    session.add(alert)
    session.commit()
    notify_farmers(f"[{alert_type.upper()}] {crop_id}: {message}")
