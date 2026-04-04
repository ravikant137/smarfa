import base64, io, json, requests, time
from PIL import Image
import random

print("Generating test image...")
# Smaller heavily diseased leaf
img = Image.new('RGB', (200, 200))
pixels = img.load()
random.seed(42)
for x in range(200):
    for y in range(200):
        r, g, b = 55, 110, 40  # green base
        d1 = ((x-60)**2 + (y-50)**2)
        if d1 < 1500: r, g, b = 130, 70, 25  # brown
        d2 = ((x-150)**2 + (y-130)**2)
        if d2 < 1200: r, g, b = 100, 55, 20  # dark brown
        if d1 < 400: r, g, b = 40, 25, 15  # necrotic center
        d3 = ((x-30)**2 + (y-150)**2)
        if d3 < 800: r, g, b = 170, 160, 50  # yellow
        pixels[x, y] = (r, g, b)

buf = io.BytesIO()
img.save(buf, format='JPEG')
b64 = base64.b64encode(buf.getvalue()).decode()

print(f"Image size: {len(buf.getvalue())} bytes")
print("Sending to /analyze_crop...")
start = time.time()
r = requests.post('http://localhost:8000/analyze_crop', json={'image_base64': b64}, timeout=300)
elapsed = time.time() - start
print(f"Status: {r.status_code} (took {elapsed:.1f}s)")
print(json.dumps(r.json(), indent=2))
