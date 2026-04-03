from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

out = Path('mobile-app/screenshots')
out.mkdir(parents=True, exist_ok=True)

def create_gradient_background(width, height, color1, color2):
    """Create a gradient background"""
    img = Image.new('RGB', (width, height), color1)
    draw = ImageDraw.Draw(img)
    for y in range(height):
        r = int(color1[0] + (color2[0] - color1[0]) * y / height)
        g = int(color1[1] + (color2[1] - color1[1]) * y / height)
        b = int(color1[2] + (color2[2] - color1[2]) * y / height)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    return img

def create_login_screen():
    img = create_gradient_background(1080, 1920, (34, 139, 34), (25, 25, 112))
    draw = ImageDraw.Draw(img)

    try:
        font_large = ImageFont.truetype('arial.ttf', 80)
        font_medium = ImageFont.truetype('arial.ttf', 50)
        font_small = ImageFont.truetype('arial.ttf', 35)
    except Exception:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Title
    draw.text((540, 200), 'Smart AI Farming', fill=(255, 255, 255), font=font_large, anchor='mm')

    # Login form mockup
    draw.rectangle([200, 400, 880, 550], fill=(255, 255, 255, 128), outline=(255, 255, 255))
    draw.text((250, 450), '👤 Username', fill=(0, 0, 0), font=font_medium)

    draw.rectangle([200, 600, 880, 750], fill=(255, 255, 255, 128), outline=(255, 255, 255))
    draw.text((250, 650), '🔒 Password', fill=(0, 0, 0), font=font_medium)

    # Animated button
    draw.rectangle([300, 850, 780, 950], fill=(255, 215, 0), outline=(255, 255, 255))
    draw.text((540, 900), 'Login', fill=(0, 0, 0), font=font_large, anchor='mm')

    draw.text((540, 1100), 'New User? Register Here', fill=(255, 255, 255), font=font_small, anchor='mm')

    return img

def create_register_screen():
    img = create_gradient_background(1080, 1920, (34, 139, 34), (25, 25, 112))
    draw = ImageDraw.Draw(img)

    try:
        font_large = ImageFont.truetype('arial.ttf', 80)
        font_medium = ImageFont.truetype('arial.ttf', 50)
        font_small = ImageFont.truetype('arial.ttf', 35)
    except Exception:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Title
    draw.text((540, 150), 'Create Account', fill=(255, 255, 255), font=font_large, anchor='mm')

    # Register form mockup
    draw.rectangle([200, 300, 880, 400], fill=(255, 255, 255, 128), outline=(255, 255, 255))
    draw.text((250, 330), '👤 Full Name', fill=(0, 0, 0), font=font_medium)

    draw.rectangle([200, 450, 880, 550], fill=(255, 255, 255, 128), outline=(255, 255, 255))
    draw.text((250, 480), '📧 Email', fill=(0, 0, 0), font=font_medium)

    draw.rectangle([200, 600, 880, 700], fill=(255, 255, 255, 128), outline=(255, 255, 255))
    draw.text((250, 630), '🔒 Password', fill=(0, 0, 0), font=font_medium)

    draw.rectangle([200, 750, 880, 850], fill=(255, 255, 255, 128), outline=(255, 255, 255))
    draw.text((250, 780), '🔒 Confirm Password', fill=(0, 0, 0), font=font_medium)

    # Animated button
    draw.rectangle([300, 950, 780, 1050], fill=(255, 215, 0), outline=(255, 255, 255))
    draw.text((540, 1000), 'Register', fill=(0, 0, 0), font=font_large, anchor='mm')

    draw.text((540, 1150), 'Already have account? Login', fill=(255, 255, 255), font=font_small, anchor='mm')

    return img

def create_home_screen():
    img = create_gradient_background(1080, 1920, (34, 139, 34), (25, 25, 112))
    draw = ImageDraw.Draw(img)

    try:
        font_large = ImageFont.truetype('arial.ttf', 80)
        font_medium = ImageFont.truetype('arial.ttf', 50)
        font_small = ImageFont.truetype('arial.ttf', 35)
    except Exception:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Header
    draw.text((540, 100), '🌾 Farm Dashboard', fill=(255, 255, 255), font=font_large, anchor='mm')

    # Stats grid
    stats = [
        ('🌱', 'Crops\nMonitored', '12'),
        ('⚠️', 'Active\nAlerts', '3'),
        ('📊', 'Growth\nRate', '85%'),
        ('💧', 'Water\nUsage', '2.3L')
    ]

    for i, (icon, label, value) in enumerate(stats):
        x = 200 + (i % 2) * 340
        y = 250 + (i // 2) * 300

        draw.rectangle([x, y, x+280, y+250], fill=(255, 255, 255, 180), outline=(255, 255, 255))
        draw.text((x+140, y+50), icon, font=font_large, anchor='mm')
        draw.text((x+140, y+120), label, fill=(0, 0, 0), font=font_medium, anchor='mm')
        draw.text((x+140, y+180), value, fill=(34, 139, 34), font=font_large, anchor='mm')

    # Navigation
    draw.rectangle([200, 1600, 440, 1700], fill=(255, 215, 0), outline=(255, 255, 255))
    draw.text((320, 1650), '🏠 Home', fill=(0, 0, 0), font=font_medium, anchor='mm')

    draw.rectangle([480, 1600, 720, 1700], fill=(255, 255, 255, 128), outline=(255, 255, 255))
    draw.text((600, 1650), '🚨 Alerts', fill=(0, 0, 0), font=font_medium, anchor='mm')

    return img

def create_alerts_screen():
    img = create_gradient_background(1080, 1920, (34, 139, 34), (25, 25, 112))
    draw = ImageDraw.Draw(img)

    try:
        font_large = ImageFont.truetype('arial.ttf', 80)
        font_medium = ImageFont.truetype('arial.ttf', 50)
        font_small = ImageFont.truetype('arial.ttf', 35)
    except Exception:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Header
    draw.text((540, 100), '🚨 Expert Alerts', fill=(255, 255, 255), font=font_large, anchor='mm')

    # Alert items
    alerts = [
        ('🔴', 'Nutrient Deficiency', 'Low nitrogen detected. Solution: Apply urea fertilizer at 50kg/ha immediately...'),
        ('🟡', 'Water Stress', 'Soil moisture below 30%. Solution: Irrigate with drip system for 2 hours...'),
        ('🟢', 'Growth Optimal', 'Corn height increasing steadily. Continue current watering schedule.')
    ]

    for i, (icon, title, desc) in enumerate(alerts):
        y = 250 + i * 350
        color = (255, 100, 100) if icon == '🔴' else (255, 200, 0) if icon == '🟡' else (100, 255, 100)

        draw.rectangle([100, y, 980, y+300], fill=(255, 255, 255, 200), outline=color, width=3)
        draw.text((150, y+50), icon, font=font_large)
        draw.text((200, y+50), title, fill=(0, 0, 0), font=font_medium)
        draw.text((150, y+120), desc[:80] + '...', fill=(0, 0, 0), font=font_small)

    # Navigation
    draw.rectangle([200, 1600, 440, 1700], fill=(255, 255, 255, 128), outline=(255, 255, 255))
    draw.text((320, 1650), '🏠 Home', fill=(0, 0, 0), font=font_medium, anchor='mm')

    draw.rectangle([480, 1600, 720, 1700], fill=(255, 215, 0), outline=(255, 255, 255))
    draw.text((600, 1650), '🚨 Alerts', fill=(0, 0, 0), font=font_medium, anchor='mm')

    return img

# Generate screenshots
screenshots = [
    ('LoginScreen.png', create_login_screen),
    ('RegisterScreen.png', create_register_screen),
    ('HomeScreen.png', create_home_screen),
    ('AlertsScreen.png', create_alerts_screen)
]

for name, create_func in screenshots:
    img = create_func()
    img.save(out / name)
    print(f'Created enhanced screenshot: {name}')

print(f'Updated UI screenshots saved in {out}')
