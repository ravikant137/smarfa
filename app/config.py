import os

class Settings:
    def __init__(self):
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.twilio_from_number = os.getenv("TWILIO_FROM_NUMBER", "+1234567890")
        self.farmer_phone_numbers = [p.strip() for p in os.getenv("FARMER_PHONE_NUMBERS", "+10000000000").split(",") if p.strip()]
        self.growth_rate_min = float(os.getenv("GROWTH_RATE_MIN", "0.05"))
        self.intrusion_motion_threshold = int(os.getenv("INTRUSION_MOTION_THRESHOLD", "1"))

settings = Settings()
