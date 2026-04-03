from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

out = Path('mobile-app/screenshots')
out.mkdir(parents=True, exist_ok=True)
images = [
    ('LoginScreen.png', 'Login Screen\n(smoketest placeholder)'),
    ('RegisterScreen.png', 'Register Screen\n(smoketest placeholder)'),
    ('HomeScreen.png', 'Home Screen\n(smoketest placeholder)'),
    ('AlertsScreen.png', 'Alerts Screen\n(smoketest placeholder)')
]

for name, text in images:
    img = Image.new('RGB', (1080, 1920), (12, 35, 85))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype('arial.ttf', 60)
    except Exception:
        font = ImageFont.load_default()
    draw.text((80, 200), text, fill=(255, 255, 255), font=font)
    img.save(out / name)

print('created placeholder screenshot images in', out)
