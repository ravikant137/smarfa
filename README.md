# Smart AI Farming (smarfa)

Smart AI Farming is a comprehensive platform to monitor crop growth end-to-end with expert-level alerts and a beautiful mobile app interface:

## Features

### Backend API
- Data ingestion API (`/sensor_data`) for crop growth and security sensor readings
- Growth tracking, trend analysis, and expert alert generation with farming solutions
- Intrusion detection and farmer notification (SMS via Twilio integration)
- SQLite persistence + modular Python architecture
- Extensible to real sensor feeds (MQTT, LoRaWAN, NB-IoT)

### Mobile App (React Native + Expo)
- **Attractive Animated UI**: Gradient backgrounds, smooth animations, and professional design
- **Login/Register Screens**: Secure authentication with animated transitions
- **Home Dashboard**: Real-time crop monitoring stats with icons and visual indicators
- **Expert Alerts**: AI-powered farming alerts with 30+ years of agricultural expertise and actionable solutions
- **Push Notifications**: Mobile alerts for critical farming events
- **Cross-platform**: iOS, Android, and Web support

## Screenshots

Check out the latest UI screenshots in `mobile-app/screenshots/`:
- `LoginScreen.png` - Animated login with gradient background
- `RegisterScreen.png` - Slide-in registration form
- `HomeScreen.png` - Dashboard with crop stats and navigation
- `AlertsScreen.png` - Expert farming alerts with solutions

## Quick Setup

### Backend Setup

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

### Mobile App Setup

1. Ensure Node.js >= 20.19.4 is installed (update if needed):

```bash
# Check version
node --version

# If outdated, download latest LTS from https://nodejs.org/
```

2. Install mobile app dependencies:

```bash
cd mobile-app
npm install
```

### Android Emulator Setup

To run the app on Android emulator instead of Expo Go:

1. **Install Android Studio**:
   ```bash
   # Download from: https://developer.android.com/studio
   # Install Android Studio with Android SDK
   ```

2. **Run setup script**:
   ```bash
   # Run the setup script to configure environment
   .\setup_android.bat
   ```

3. **Create Android Virtual Device**:
   - Open Android Studio
   - Tools → Device Manager
   - Create Virtual Device (Pixel 6, API 33+)

4. **Run on Android emulator**:
   ```bash
   cd mobile-app
   npx expo start --android
   ```

### Alternative: Use Expo Go (Easier)

For quick testing, use Expo Go app on your phone:
```bash
cd mobile-app
npx expo start
# Scan QR code with Expo Go app
```

## API Testing

### Backend Tests

Send test sensor payload:

```bash
curl -X POST http://127.0.0.1:8000/sensor_data -H "Content-Type: application/json" -d "{\"crop_id\":\"field-1\",\"type\":\"growth\",\"height_cm\":30.1,\"soil_moisture\":45.2,\"temperature_c\":28.1}"
```

Check expert alerts:

```bash
curl http://127.0.0.1:8000/alerts
```

### Mobile Integration

Register device token:

```bash
curl -X POST http://127.0.0.1:8000/mobile/register -H "Content-Type: application/json" -d "{\"farmer_id\":\"farmer-1\",\"device_token\":\"abc123token\"}"
```

List registered devices:

```bash
curl http://127.0.0.1:8000/mobile/devices
```

Send test push to mobile:

```bash
curl -X POST http://127.0.0.1:8000/mobile/send_push -H "Content-Type: application/json" -d "{\"farmer_id\":\"farmer-1\",\"title\":\"Test Alert\",\"body\":\"Crop growth update available\"}"
```

## Architecture

- **Backend**: FastAPI with SQLAlchemy ORM, Pydantic models, expert alert logic
- **Database**: SQLite for development, easily upgradeable to PostgreSQL/MySQL
- **Mobile**: React Native with Expo, React Navigation, Axios for API calls
- **UI**: Linear gradients, vector icons, smooth animations with Reanimated
- **Alerts**: Expert farming advice based on 30+ years agricultural experience

## Development

### Running Tests

```bash
# Backend tests
python -m pytest

# Generate updated screenshots
python generate_screenshots.py
```

### Project Structure

```
smarfa/
├── app/                    # FastAPI backend
│   ├── main.py            # Main API endpoints
│   ├── models.py          # SQLAlchemy models
│   ├── database.py        # Database configuration
│   ├── sensors.py         # Expert alert processing
│   └── alerts.py          # SMS/Push notification logic
├── mobile-app/            # React Native app
│   ├── App.js             # App entry point
│   ├── navigation/        # Navigation setup
│   ├── screens/           # UI screens (Login, Register, Home, Alerts)
│   ├── components/        # Reusable components
│   └── screenshots/       # UI screenshots
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

