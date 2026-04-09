# SmartFarm AI 🌾

**Offline crop disease detection and treatment advice powered by deep learning.**

Detects plant diseases from leaf images using transfer learning (EfficientNetB0) and provides farmer-friendly treatment advice in multiple languages — all without internet after initial setup.

---

## Project Structure

```
smartfarm-ai/
├── dataset/                  # Place PlantVillage dataset here
├── model/
│   ├── smartfarm_model.h5    # Trained Keras model
│   ├── smartfarm_model.tflite# Quantized mobile model
│   └── class_names.json      # Class label mapping
├── api/
│   └── app.py                # FastAPI backend
├── training/
│   ├── train.py              # Training pipeline
│   └── tflite_convert.py     # TFLite conversion + inference demo
├── utils/
│   ├── preprocess.py         # Image augmentation & preprocessing
│   └── advice.py             # Multilingual advice engine
├── requirements.txt
└── README.md
```

---

## Step-by-Step Setup

### Step 1: Create a virtual environment

```bash
cd smartfarm-ai
python3 -m venv venv
source venv/bin/activate       # Linux/Mac
# venv\Scripts\activate        # Windows
```

### Step 2: Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Prepare the dataset

Download the **PlantVillage** dataset and place it inside the `dataset/` folder. The directory structure should look like:

```
dataset/
├── Tomato___Bacterial_spot/
│   ├── image001.jpg
│   ├── image002.jpg
│   └── ...
├── Tomato___Early_blight/
│   └── ...
├── Tomato___healthy/
│   └── ...
└── ... (other classes)
```

**Download options:**
- Kaggle: https://www.kaggle.com/datasets/emmarex/plantdisease
- Or use `tensorflow_datasets`:
  ```python
  import tensorflow_datasets as tfds
  ds = tfds.load('plant_village', split='train')
  ```

You can also add **your own farmer images** into the appropriate class folders for incremental learning.

---

## Step 4: Train the Model

```bash
python training/train.py --dataset dataset/ --batch-size 32
```

**Options:**
| Flag | Description | Default |
|------|-------------|---------|
| `--dataset` | Path to dataset directory | `dataset/` |
| `--batch-size` | Training batch size | `32` |
| `--skip-tflite` | Skip TFLite conversion | `False` |
| `--convert-only` | Only convert .h5 → .tflite | `False` |

**What happens:**
1. **Phase 1** – Trains the custom classification head (base frozen) for up to 15 epochs
2. **Phase 2** – Fine-tunes the last layers of EfficientNetB0 for up to 20 epochs
3. **Evaluation** – Prints accuracy, confusion matrix, and classification report
4. **Export** – Saves `.h5` and `.tflite` models to `model/`

**Target: >90% validation accuracy**

---

## Step 5: Start the API Server

```bash
cd api
uvicorn app:app --host 0.0.0.0 --port 8000
```

The server runs at: **http://localhost:8000**

API docs available at: **http://localhost:8000/docs**

---

## Step 6: Test the API

### Using curl:

```bash
curl -X POST http://localhost:8000/predict \
  -F "file=@path/to/leaf_image.jpg" \
  -F "lang=en"
```

### Using Python:

```python
import requests

url = "http://localhost:8000/predict"
files = {"file": open("leaf_image.jpg", "rb")}
params = {"lang": "en"}   # en, hi, kn

response = requests.post(url, files=files, params=params)
print(response.json())
```

### Sample Response:

```json
{
  "disease": "Tomato___Early_blight",
  "confidence": 0.9542,
  "solution": "Apply chlorothalonil or mancozeb fungicide. Remove lower infected leaves. Ensure proper plant spacing for air circulation. Mulch around base of plants.",
  "language_support": "en"
}
```

### Other Endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API status |
| GET | `/health` | Model load status |
| GET | `/diseases` | List all known diseases & languages |
| POST | `/predict` | Upload image → get prediction |

---

## Step 7: TFLite for Mobile

### Convert only (if model already trained):

```bash
python training/train.py --convert-only
```

### Or use the dedicated script:

```bash
python training/tflite_convert.py convert --model model/smartfarm_model.h5 --output model/smartfarm_model.tflite
```

### Test TFLite inference:

```bash
python training/tflite_convert.py predict path/to/leaf_image.jpg
```

### Mobile Integration (Android/iOS):

The `.tflite` model can be loaded in mobile apps using:
- **Android**: TensorFlow Lite Android Support Library
- **iOS**: TensorFlow Lite Swift/ObjC API
- **Flutter**: `tflite_flutter` package

```java
// Android example (Java)
Interpreter interpreter = new Interpreter(loadModelFile("smartfarm_model.tflite"));
float[][] output = new float[1][NUM_CLASSES];
interpreter.run(inputImage, output);
```

---

## Multilingual Support

The advice engine supports:

| Code | Language |
|------|----------|
| `en` | English |
| `hi` | Hindi |
| `kn` | Kannada |

Pass `lang=hi` to the `/predict` endpoint or `get_advice()` function.

To add a new language, edit `utils/advice.py` and add entries to the `DISEASE_ADVICE` dictionary.

---

## Performance Notes

- **Mixed precision** is auto-enabled when a GPU is detected
- **EfficientNetB0** provides a good accuracy/size tradeoff (~4M params)
- **TFLite quantization** reduces model size by ~50% with minimal accuracy loss
- Preprocessing pipeline includes noise/blur augmentation for robustness to real-world conditions

---

## Future Extensions

The system is designed with hooks for:

- **Crop recommendation** – Add a `/recommend` endpoint that takes soil/weather data
- **Yield prediction** – Extend with regression model on weather + soil features
- **Pest detection** – Add object detection model (YOLO/SSD) for insect identification
- **Offline voice assistant** – Integrate with offline STT/TTS (e.g., Vosk + pyttsx3) for multilingual voice interaction

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| ML Framework | TensorFlow / Keras |
| Base Model | EfficientNetB0 (ImageNet pretrained) |
| Backend | FastAPI + Uvicorn |
| Image Processing | PIL, NumPy |
| Mobile | TensorFlow Lite (float16 quantized) |
| Advice Engine | Offline dictionary (no LLM) |

**Zero paid APIs. Fully offline after setup.**
