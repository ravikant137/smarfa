# Smart AI Farming (smarfa)

Smart AI Farming is a prototype platform to monitor crop growth end-to-end and provide real-time alerts for:
- Growth status deviations (nutrient deficit, water stress, stunted growth)
- Intrusion/security alarms (unauthorized entry events)
- Notification push to farmers via SMS (Twilio integration)

## Features

- Data ingestion API (`/sensor_data`) for crop growth and security sensor readings
- Growth tracking, trend analysis, and alert generation
- Intrusion detection and farmer notification (mobile alerts via SMS)
- SQLite persistence + modular Python architecture
- Extensible to real sensor feeds (MQTT, LoRaWAN, NB-IoT)

## Quick setup

1. Create a Python virtual environment:

```bash
python -m venv .venv
.\.venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment variables (copy `.env.example`):

```bash
copy .env.example .env
```

4. Run API server:

```bash
uvicorn app.main:app --reload
```

5. Send test sensor payload:

```bash
curl -X POST http://127.0.0.1:8000/sensor_data -H "Content-Type: application/json" -d "{\"crop_id\":\"field-1\",\"type\":\"growth\",\"height_cm\":30.1,\"soil_moisture\":45.2,\"temperature_c\":28.1}"
```

6. Check alerts:

```bash
curl http://127.0.0.1:8000/alerts
```

## Mobile app integration (sample)

- Register device token:

```bash
curl -X POST http://127.0.0.1:8000/mobile/register -H "Content-Type: application/json" -d "{\"farmer_id\":\"farmer-1\",\"device_token\":\"abc123token\"}"
```

- List registered devices:

```bash
curl http://127.0.0.1:8000/mobile/devices
```

- Send test push to mobile:

```bash
curl -X POST http://127.0.0.1:8000/mobile/send_push -H "Content-Type: application/json" -d "{\"farmer_id\":\"farmer-1\",\"title\":\"Test Alert\",\"body\":\"Crop growth update available\"}"
```

