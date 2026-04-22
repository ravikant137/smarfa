from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import os

app = FastAPI()

# Mount static files relative to the script location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

METRICS_FILE = "metrics.json"

def get_latest_metrics():
    if not os.path.exists(METRICS_FILE):
        return {
            "status": "waiting",
            "epoch": 0,
            "train_loss": [],
            "val_accuracy_binary": [],
            "val_accuracy_species": [],
            "confusion_matrix": None
        }
    with open(METRICS_FILE, "r") as f:
        return json.load(f)

@app.get("/", response_class=HTMLResponse)
async def read_dashboard():
    dashboard_path = os.path.join(BASE_DIR, "static", "dashboard.html")
    with open(dashboard_path, "r") as f:
        return f.read()

@app.get("/api/metrics")
async def get_metrics():
    return JSONResponse(content=get_latest_metrics())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
