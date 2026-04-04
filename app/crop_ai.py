"""
Crop image analysis using FREE AI — no API keys required.

Pipeline:
  1. Ollama vision model (moondream/llava) — best results, needs RAM
  2. PIL color analysis + Ollama text LLM (tinyllama) for AI description
  3. PIL-only fallback (always works, no dependencies beyond Pillow)
  4. Agricultural knowledge base for expert recommendations
"""

import base64
import io
import os
import json
import logging

logger = logging.getLogger(__name__)

OLLAMA_BASE = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Vision models need >6GB RAM. Set SMARFA_VISION=1 to enable on capable machines.
_VISION_ENABLED = os.getenv("SMARFA_VISION", "0") == "1"
_vision_failed_count = 0  # Track failures to auto-disable


# ── Agricultural Knowledge Base ───────────────────────────────────────────
DISEASE_KNOWLEDGE = {
    "Tomato___Late_blight": {
        "crop": "Tomato",
        "disease": "Late Blight",
        "severity": "critical",
        "description": "Caused by Phytophthora infestans. Dark, water-soaked lesions on leaves and stems that rapidly enlarge.",
        "recommendations": [
            "Remove and destroy all infected plant material immediately.",
            "Apply copper-based fungicide (Bordeaux mixture) as preventive spray.",
            "Improve air circulation by proper spacing (60-90cm between plants).",
            "Avoid overhead irrigation; use drip irrigation instead.",
            "Apply chlorothalonil or mancozeb fungicide every 7-10 days during wet weather.",
        ],
        "growth_needs": "Full sun 8+ hours, well-drained soil pH 6.0-6.8, consistent moisture, 21-29°C.",
    },
    "Tomato___Early_blight": {
        "crop": "Tomato",
        "disease": "Early Blight",
        "severity": "warning",
        "description": "Caused by Alternaria solani. Concentric ring-shaped brown spots on older leaves.",
        "recommendations": [
            "Remove lower infected leaves to prevent spread upward.",
            "Mulch around base to prevent soil splash onto leaves.",
            "Apply neem oil or copper fungicide every 7-14 days.",
            "Rotate crops — don't plant tomatoes in the same spot for 3 years.",
            "Ensure adequate potassium levels in soil to strengthen plant immunity.",
        ],
        "growth_needs": "Consistent watering, balanced fertilizer (10-10-10) every 2 weeks.",
    },
    "Tomato___Bacterial_spot": {
        "crop": "Tomato", "disease": "Bacterial Spot", "severity": "warning",
        "description": "Small, dark, raised spots on leaves, stems and fruit.",
        "recommendations": [
            "Remove and destroy infected plants.", "Apply copper-based bactericide.",
            "Use disease-free seed and transplants.", "Avoid working with wet plants.",
            "Practice crop rotation with non-solanaceous crops.",
        ],
        "growth_needs": "Keep foliage dry, air circulation, soil pH 6.2-6.8.",
    },
    "Tomato___healthy": {
        "crop": "Tomato", "disease": None, "severity": "healthy",
        "description": "Healthy tomato plant with good leaf color and structure.",
        "recommendations": [
            "Continue regular watering: 1-2 inches/week at soil level.",
            "Apply balanced fertilizer (10-10-10) every 2-3 weeks.",
            "Monitor for pests — check leaf undersides weekly.",
            "Stake or cage plants for support as fruit develops.",
            "Prune suckers to improve air circulation and fruit production.",
        ],
        "growth_needs": "Full sun 8+ hours, soil pH 6.0-6.8, consistent moisture, 21-29°C.",
    },
    "Potato___Late_blight": {
        "crop": "Potato", "disease": "Late Blight", "severity": "critical",
        "description": "Dark water-soaked lesions, white fungal growth. Can destroy entire crop.",
        "recommendations": [
            "Destroy all infected foliage and tubers.", "Apply mancozeb/chlorothalonil during humid weather.",
            "Hill potatoes well to protect tubers.", "Harvest on dry days, cure before storage.",
            "Plant certified disease-free seed potatoes.",
        ],
        "growth_needs": "Cool climate 15-20°C, well-drained soil, pH 5.0-6.0.",
    },
    "Potato___healthy": {
        "crop": "Potato", "disease": None, "severity": "healthy",
        "description": "Healthy potato plant with vigorous green foliage.",
        "recommendations": [
            "Continue hilling soil around stems.", "Maintain 1-2 inches water/week.",
            "Apply potassium-rich fertilizer near flowering.", "Monitor for Colorado potato beetle weekly.",
            "Plan harvest 2-3 weeks after foliage dies back.",
        ],
        "growth_needs": "Cool temps 15-20°C, loose soil, pH 5.0-6.0, high potassium.",
    },
    "Corn___Common_rust": {
        "crop": "Corn", "disease": "Common Rust", "severity": "warning",
        "description": "Cinnamon-brown pustules on both leaf surfaces reducing photosynthesis.",
        "recommendations": [
            "Plant rust-resistant varieties.", "Apply triazole fungicide if severe.",
            "Ensure adequate plant spacing.", "Remove heavily infected leaves.",
            "Rotate with non-grass crops.",
        ],
        "growth_needs": "Full sun, deep soil, 200kg N/ha in splits, consistent water during tasseling.",
    },
    "Corn___healthy": {
        "crop": "Corn", "disease": None, "severity": "healthy",
        "description": "Vigorous corn growth with good green color and leaf structure.",
        "recommendations": [
            "Apply side-dress nitrogen at V6-V8 stage.", "Irrigate during silking and grain fill.",
            "Scout for armyworm and corn borer weekly.", "Maintain weed-free rows first 6 weeks.",
            "Harvest when kernels reach black layer (30% moisture).",
        ],
        "growth_needs": "Heavy nitrogen 200-250 kg/ha, full sun, soil temp >10°C, 500-800mm water.",
    },
    "Rice___Brown_spot": {
        "crop": "Rice", "disease": "Brown Spot", "severity": "warning",
        "description": "Oval brown spots with gray centers, associated with nutrient-deficient soils.",
        "recommendations": [
            "Apply silicon-based fertilizer.", "Correct potassium/manganese deficiency.",
            "Treat seed with fungicide.", "Apply propiconazole at boot stage.",
            "Maintain proper water level in paddy.",
        ],
        "growth_needs": "Standing water 5-10cm, soil pH 5.5-6.5, balanced NPK + silicon, 25-35°C.",
    },
    "Rice___Leaf_blast": {
        "crop": "Rice", "disease": "Leaf Blast", "severity": "critical",
        "description": "Diamond-shaped lesions on leaves. Can devastate entire fields rapidly.",
        "recommendations": [
            "Plant blast-resistant varieties.", "Reduce excess nitrogen.",
            "Apply tricyclazole preventively.", "Maintain adequate water levels.",
            "Avoid late planting.",
        ],
        "growth_needs": "Controlled flooding, moderate nitrogen, silicon supplementation, 24-28°C.",
    },
    "Grape___Black_rot": {
        "crop": "Grape", "disease": "Black Rot", "severity": "critical",
        "description": "Reddish-brown circular leaf spots, fruit becomes hard black mummies.",
        "recommendations": [
            "Remove all mummified fruit.", "Apply myclobutanil/mancozeb from bud break.",
            "Maintain open canopy.", "Remove wild grapes nearby.",
            "Spray every 10-14 days from 10-inch shoot growth.",
        ],
        "growth_needs": "Full sun, well-drained soil pH 5.5-6.5, annual pruning, 600-800mm rainfall.",
    },
    "Apple___Apple_scab": {
        "crop": "Apple", "disease": "Apple Scab", "severity": "warning",
        "description": "Olive-green to brown velvety spots on leaves and fruit.",
        "recommendations": [
            "Rake/destroy fallen leaves in autumn.", "Apply captan from green tip through petal fall.",
            "Plant scab-resistant varieties.", "Prune for open canopy.",
            "Apply 5% urea spray to fallen leaves in autumn.",
        ],
        "growth_needs": "Full sun, well-drained soil pH 6.0-7.0, annual pruning, 800-1200 chill hours.",
    },
    "Wheat___healthy": {
        "crop": "Wheat", "disease": None, "severity": "healthy",
        "description": "Healthy wheat with good tiller development and green coloration.",
        "recommendations": [
            "Top-dress nitrogen at tillering and stem elongation.", "Monitor for aphids and rust weekly.",
            "Maintain moisture during grain fill.", "Scout for weeds, apply selective herbicide.",
            "Plan harvest at 13-14% grain moisture.",
        ],
        "growth_needs": "Cool-season 15-24°C, 300-500mm water, nitrogen-responsive, pH 6.0-7.0.",
    },
    # ── Leaf Scorch / Burn (very common — matches user's image) ──────
    "General___Leaf_scorch": {
        "crop": "General", "disease": "Leaf Scorch", "severity": "critical",
        "description": "Leaf margins and tips turn brown and papery. Often starts at edges and moves inward. Caused by drought, heat stress, root damage, or bacterial infection (Xylella fastidiosa).",
        "recommendations": [
            "Water deeply 2-3 times per week during hot/dry periods — shallow watering worsens scorch.",
            "Apply 3-4 inches of mulch around base to retain soil moisture and cool roots.",
            "Check for bacterial leaf scorch: if browning has a yellow border between brown and green, test for Xylella.",
            "Prune severely scorched branches to redirect energy to healthy growth.",
            "Provide afternoon shade for sensitive plants during extreme heat (>35°C).",
            "Ensure soil drainage — poor drainage causes root damage leading to scorch symptoms.",
        ],
        "growth_needs": "Deep watering, mulch layer, wind protection, soil pH 6.0-7.0.",
    },
    "General___Leaf_blight": {
        "crop": "General", "disease": "Leaf Blight", "severity": "critical",
        "description": "Large brown dead patches on leaves, often with dark edges. Caused by fungal pathogens (Alternaria, Helminthosporium). Spreads rapidly in warm, humid conditions.",
        "recommendations": [
            "Remove ALL infected leaves and destroy them (do NOT compost).",
            "Apply copper-based fungicide (Bordeaux mixture) immediately and repeat every 7-10 days.",
            "Avoid overhead watering — use drip irrigation to keep foliage dry.",
            "Ensure plant spacing for air circulation (minimum 30cm between plants).",
            "Apply potassium-rich fertilizer to strengthen plant cell walls against infection.",
            "Rotate crops for 2-3 seasons — blight pathogens persist in soil.",
        ],
        "growth_needs": "Dry foliage, good air flow, balanced nutrients with extra K, avoid nitrogen excess.",
    },
    "General___Anthracnose": {
        "crop": "General", "disease": "Anthracnose", "severity": "warning",
        "description": "Dark, sunken lesions on leaves, stems, and fruit. Caused by Colletotrichum fungi. Spreads via rain splash.",
        "recommendations": [
            "Prune infected branches 6 inches below visible symptoms.",
            "Apply chlorothalonil or copper fungicide in early spring.",
            "Rake and destroy fallen infected leaves.",
            "Avoid overhead irrigation; water at soil level.",
            "Maintain proper plant spacing for air circulation.",
        ],
        "growth_needs": "Avoid wet foliage, good drainage, pruning for open canopy.",
    },
    "General___Septoria_leaf_spot": {
        "crop": "General", "disease": "Septoria Leaf Spot", "severity": "warning",
        "description": "Circular spots with dark edges and light gray centers containing tiny black dots (pycnidia). Starts on lower leaves.",
        "recommendations": [
            "Remove lower infected leaves immediately.",
            "Apply mancozeb or chlorothalonil fungicide every 7-14 days.",
            "Mulch around plant base to prevent rain splash.",
            "Stake plants upright to improve air circulation.",
            "Water at base — never wet the foliage.",
        ],
        "growth_needs": "Dry foliage, mulched soil, crop rotation, disease-free seed.",
    },
    "General___Cercospora_leaf_spot": {
        "crop": "General", "disease": "Cercospora Leaf Spot", "severity": "warning",
        "description": "Small circular spots with reddish-purple borders and tan/gray centers. Common in warm humid weather.",
        "recommendations": [
            "Remove and destroy infected leaves.",
            "Apply azoxystrobin or propiconazole fungicide.",
            "Improve air circulation with proper spacing.",
            "Avoid overhead watering in evening.",
            "Rotate crops — don't replant same family for 2 years.",
        ],
        "growth_needs": "Good air flow, morning watering, balanced fertility, crop rotation.",
    },
    "General___Nutrient_deficiency": {
        "crop": "General", "disease": "Nutrient Deficiency", "severity": "warning",
        "description": "Yellowing, purpling, or browning of leaves indicating lack of essential nutrients.",
        "recommendations": [
            "Test soil immediately for N, P, K, Fe, Mn, and Mg levels.",
            "Apply balanced NPK fertilizer (10-10-10) as immediate relief.",
            "For yellowing: add nitrogen (urea or ammonium sulfate).",
            "For inter-veinal yellowing: apply chelated iron/manganese.",
            "Adjust soil pH to 6.0-7.0 — nutrients lock out at wrong pH.",
            "Add organic matter (compost) to improve nutrient retention.",
        ],
        "growth_needs": "Soil pH 6.0-7.0, regular fertilization, organic matter, micronutrients.",
    },
    "General___Drought_stress": {
        "crop": "General", "disease": "Drought Stress", "severity": "warning",
        "description": "Leaf wilting, curling, and browning from edges inward. Soil is dry and cracked.",
        "recommendations": [
            "Water deeply and immediately — soak the root zone thoroughly.",
            "Apply 3-4 inches mulch to reduce evaporation.",
            "Set up drip irrigation on timer for consistent moisture.",
            "Avoid fertilizing stressed plants — wait until recovery.",
            "Consider shade cloth during extreme heat (>38°C).",
        ],
        "growth_needs": "1-2 inches water per week minimum, mulch, shade in extreme heat.",
    },
    # ── Additional crop-specific diseases ─────────────────────────────
    "Mango___Anthracnose": {
        "crop": "Mango", "disease": "Anthracnose", "severity": "critical",
        "description": "Black/brown necrotic spots on leaves and fruit. Caused by Colletotrichum gloeosporioides. Worst in humid/rainy weather.",
        "recommendations": [
            "Apply copper oxychloride or mancozeb before flowering.",
            "Prune infected branches and destroy fallen debris.",
            "Avoid overhead irrigation during flowering.",
            "Apply carbendazim at fruit set stage.",
            "Ensure good air circulation via canopy management.",
        ],
        "growth_needs": "Full sun, deep well-drained soil, pH 5.5-7.5, 25-35°C, low humidity during flowering.",
    },
    "Mango___Powdery_mildew": {
        "crop": "Mango", "disease": "Powdery Mildew", "severity": "warning",
        "description": "White powdery coating on leaves and flowers. Causes flower drop and reduces yield.",
        "recommendations": [
            "Apply sulfur-based fungicide or potassium bicarbonate spray.",
            "Spray wettable sulfur at panicle emergence.",
            "Prune for better air circulation.",
            "Apply neem oil as preventive measure.",
            "Avoid excess nitrogen fertilization.",
        ],
        "growth_needs": "Good air flow, balanced fertilizer, avoid leafy growth during flowering.",
    },
    "Citrus___Citrus_canker": {
        "crop": "Citrus", "disease": "Citrus Canker", "severity": "critical",
        "description": "Raised brown lesions with water-soaked margins on leaves, stems, and fruit.",
        "recommendations": [
            "Remove and burn severely infected branches.",
            "Apply copper-based bactericide every 3-4 weeks.",
            "Install windbreaks to reduce spread.",
            "Disinfect pruning tools between cuts.",
            "Quarantine new plants before introducing to orchard.",
        ],
        "growth_needs": "Full sun, well-drained soil pH 6.0-7.0, regular copper sprays, wind protection.",
    },
    "Pepper___Bacterial_leaf_spot": {
        "crop": "Pepper", "disease": "Bacterial Leaf Spot", "severity": "warning",
        "description": "Small, dark, water-soaked spots that enlarge and turn brown with yellow halos.",
        "recommendations": [
            "Remove infected leaves and destroy them.",
            "Apply copper hydroxide or copper sulfate spray.",
            "Use disease-free transplants and treated seed.",
            "Avoid overhead irrigation.",
            "Rotate with non-solanaceous crops for 2 years.",
        ],
        "growth_needs": "Full sun, well-drained soil pH 6.0-6.8, consistent moisture, 21-29°C.",
    },
    "Bean___Rust": {
        "crop": "Bean", "disease": "Rust Disease", "severity": "warning",
        "description": "Small reddish-brown pustules on leaf undersides. Reduces yield significantly.",
        "recommendations": [
            "Apply triazole-based fungicide at first sign of pustules.",
            "Plant rust-resistant bean varieties.",
            "Destroy crop residue after harvest.",
            "Avoid working with wet plants.",
            "Ensure adequate spacing for air circulation.",
        ],
        "growth_needs": "Full sun, well-drained soil pH 6.0-7.0, moderate watering, 18-26°C.",
    },
    "Apple___Fire_blight": {
        "crop": "Apple", "disease": "Fire Blight", "severity": "critical",
        "description": "Bacterial disease causing shoots to blacken and curl like burned. Very destructive in warm wet springs.",
        "recommendations": [
            "Cut infected branches 12 inches below visible disease during dry weather.",
            "Sterilize pruning tools with 70% alcohol between each cut.",
            "Apply streptomycin spray during bloom period.",
            "Avoid excess nitrogen which promotes susceptible growth.",
            "Remove water sprouts and suckers regularly.",
        ],
        "growth_needs": "Good drainage, moderate nitrogen, open canopy, fire blight resistant rootstock.",
    },
    "General___Powdery_mildew": {
        "crop": "General", "disease": "Powdery Mildew", "severity": "warning",
        "description": "White powdery patches on leaves and stems. Thrives in warm, dry conditions with cool nights.",
        "recommendations": [
            "Apply potassium bicarbonate or sulfur-based fungicide.",
            "Improve air circulation — thin dense plantings.",
            "Spray neem oil as organic alternative every 7-14 days.",
            "Water at base, avoid wetting foliage.",
            "Remove and destroy severely infected leaves.",
        ],
        "growth_needs": "Good air circulation, avoid overcrowding, morning watering, balanced nutrition.",
    },
    "General___Rust": {
        "crop": "General", "disease": "Rust Disease", "severity": "warning",
        "description": "Orange, yellow, or brown pustules on leaf surfaces. Caused by various Puccinia species.",
        "recommendations": [
            "Apply triazole fungicide (propiconazole or tebuconazole).",
            "Remove severely infected leaves and destroy them.",
            "Ensure adequate plant spacing for air flow.",
            "Avoid overhead irrigation.",
            "Plant resistant varieties when available.",
        ],
        "growth_needs": "Good air circulation, dry foliage, crop rotation, resistant cultivars.",
    },
}

GENERIC_KNOWLEDGE = {
    "healthy": {
        "recommendations": [
            "Continue current care — watering, fertilizing, and pest monitoring.",
            "Test soil every 6 months for nutrient levels and pH.",
            "Apply 2-3 inches organic compost as mulch.",
            "Rotate crops each season to prevent disease buildup.",
            "Keep records of planting dates, fertilizer, and yields.",
        ],
        "growth_needs": "6-8 hours sunlight, 1-2 inches water/week, soil pH 6.0-7.0, balanced NPK, good drainage.",
    },
    "diseased": {
        "recommendations": [
            "Isolate affected plants to prevent disease spread.",
            "Consult local agricultural extension office with photos.",
            "Apply broad-spectrum organic fungicide (neem oil or copper-based).",
            "Check irrigation — both over and under-watering cause disease.",
            "Test soil for nutrient deficiencies (N, K, micronutrients).",
        ],
        "growth_needs": "Fix soil health first: proper drainage, pH 6.0-7.0, adequate organic matter. Reduce nitrogen if fungal.",
    },
}


# ── Image Feature Extraction ─────────────────────────────────────────────

def extract_image_features(image_bytes: bytes) -> dict:
    """Extract comprehensive visual features from a crop image — color, texture, spatial patterns."""
    from PIL import Image, ImageFilter
    import statistics
    import math

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    # Use larger sample for better accuracy
    analysis_size = (150, 150)
    small = img.resize(analysis_size)
    pixels = list(small.getdata())
    total = len(pixels)
    width, height = analysis_size

    # ── Detailed Color Classification ─────────────────────────────────
    green = brown = yellow = dark = white = red_spots = purple = orange = 0
    dry_tan = necrotic_dark_brown = lesion_edge = 0

    for r, g, b in pixels:
        # Healthy green (vibrant)
        if g > r and g > b and g > 80 and (g - r) > 15:
            green += 1
        # Light/weak green (stressed but alive)
        elif g > r and g > b and g > 60:
            green += 0.5
        # Dark necrotic brown (dead tissue — blackish brown)
        elif r > 60 and g < 60 and b < 50 and r > g * 1.3:
            necrotic_dark_brown += 1
        # Brown / tan (dying tissue)
        elif r > g and r > 70 and g > 40 and b < g and (r - b) > 30:
            brown += 1
        # Dry tan / papery (dried dead leaves)
        elif r > 120 and g > 90 and b > 50 and (r - g) < 50 and b < g:
            dry_tan += 1
        # Lesion edges (dark border around spots)
        elif r < 80 and g < 60 and b < 50 and r > g:
            lesion_edge += 1
        # Yellow (nutrient deficiency / senescence)
        elif r > 140 and g > 140 and b < 100:
            yellow += 1
        # Orange (rust disease indicator)
        elif r > 160 and g > 80 and g < 140 and b < 80:
            orange += 1
        # Red/reddish spots (bacterial / viral indicators)
        elif r > 140 and g < 80 and b < 80:
            red_spots += 1
        # Purple (phosphorus deficiency / anthocyanins)
        elif b > g and r > g and b > 80 and r > 80:
            purple += 1
        # Dark (very dark spots, could be severe disease)
        elif r < 50 and g < 50 and b < 50:
            dark += 1
        # White (powdery mildew / bleaching)
        elif r > 200 and g > 200 and b > 200:
            white += 1

    r_vals = [p[0] for p in pixels]
    g_vals = [p[1] for p in pixels]
    b_vals = [p[2] for p in pixels]

    # ── Spatial Analysis (divide image into grid) ─────────────────────
    grid_size = 5  # 5x5 grid = 25 zones
    zone_w, zone_h = width // grid_size, height // grid_size
    zone_health = []  # 0 = unhealthy, 1 = healthy per zone

    for gy in range(grid_size):
        for gx in range(grid_size):
            zone_green = 0
            zone_brown = 0
            zone_total = 0
            for y in range(gy * zone_h, (gy + 1) * zone_h):
                for x in range(gx * zone_w, (gx + 1) * zone_w):
                    idx = y * width + x
                    if idx < total:
                        r, g, b = pixels[idx]
                        zone_total += 1
                        if g > r and g > b and g > 60:
                            zone_green += 1
                        elif (r > g and r > 70 and b < g) or (r > 60 and g < 60 and b < 50):
                            zone_brown += 1
            if zone_total > 0:
                zone_health.append(1 if zone_green / zone_total > 0.4 else 0)

    healthy_zones = sum(zone_health)
    total_zones = len(zone_health) or 1
    spread_pct = round((1 - healthy_zones / total_zones) * 100, 1)

    # ── Edge / Texture Analysis (spot detection) ──────────────────────
    gray = img.resize(analysis_size).convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edge_pixels = list(edges.getdata())
    high_edges = sum(1 for p in edge_pixels if p > 50)
    edge_density = round(high_edges / len(edge_pixels) * 100, 1)

    # Detect spots: high local contrast = lesions
    variance_filter = gray.filter(ImageFilter.Kernel((3,3), [-1,-1,-1,-1,8,-1,-1,-1,-1], scale=1, offset=128))
    var_pixels = list(variance_filter.getdata())
    high_variance = sum(1 for p in var_pixels if abs(p - 128) > 25)
    spot_density = round(high_variance / len(var_pixels) * 100, 1)

    # Total damaged tissue (all non-healthy, non-background)
    total_damaged = brown + necrotic_dark_brown + dry_tan + lesion_edge + dark + red_spots
    total_damaged_pct = round(total_damaged / total * 100, 1)

    return {
        "green_pct": round(green / total * 100, 1),
        "brown_pct": round(brown / total * 100, 1),
        "yellow_pct": round(yellow / total * 100, 1),
        "dark_pct": round(dark / total * 100, 1),
        "white_pct": round(white / total * 100, 1),
        "necrotic_pct": round(necrotic_dark_brown / total * 100, 1),
        "dry_tan_pct": round(dry_tan / total * 100, 1),
        "lesion_edge_pct": round(lesion_edge / total * 100, 1),
        "orange_pct": round(orange / total * 100, 1),
        "red_pct": round(red_spots / total * 100, 1),
        "purple_pct": round(purple / total * 100, 1),
        "total_damaged_pct": total_damaged_pct,
        "damage_spread_pct": spread_pct,
        "edge_density": edge_density,
        "spot_density": spot_density,
        "avg_r": round(statistics.mean(r_vals), 1),
        "avg_g": round(statistics.mean(g_vals), 1),
        "avg_b": round(statistics.mean(b_vals), 1),
        "std_r": round(statistics.stdev(r_vals) if len(r_vals) > 1 else 0, 1),
        "std_g": round(statistics.stdev(g_vals) if len(g_vals) > 1 else 0, 1),
        "std_b": round(statistics.stdev(b_vals) if len(b_vals) > 1 else 0, 1),
    }


# ── Analysis Engines ──────────────────────────────────────────────────────

async def _try_vision_models(image_base64: str) -> dict | None:
    """Try Ollama vision models with compressed images for better RAM usage."""
    global _vision_failed_count
    import httpx
    from PIL import Image

    # Skip if vision disabled or failed too many times
    if not _VISION_ENABLED or _vision_failed_count >= 2:
        logger.info("Vision models skipped (disabled or failed %d times)", _vision_failed_count)
        return None

    # Quick check: try to ping Ollama first
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{OLLAMA_BASE}/api/tags")
            if r.status_code != 200:
                return None
    except Exception:
        logger.info("Ollama not reachable")
        return None

    # Compress image to reduce RAM usage (224x224 JPEG, quality 60)
    try:
        raw_bytes = base64.b64decode(image_base64)
        img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
        img = img.resize((224, 224))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=60)
        compressed_b64 = base64.b64encode(buf.getvalue()).decode()
        logger.info("Compressed image: %d -> %d bytes", len(raw_bytes), len(buf.getvalue()))
    except Exception:
        compressed_b64 = image_base64

    prompt = """You are an expert agricultural scientist. Analyze this crop/plant image carefully.

Respond ONLY with valid JSON (no extra text):
{
  "crop": "exact crop/plant name (e.g. Apple, Tomato, Potato, Corn, Grape, Wheat, Rice, Mango, Citrus, etc.)",
  "disease": "exact disease name or null if healthy",
  "severity": "critical or warning or healthy",
  "description": "detailed 2-3 sentence analysis of what you see — describe leaf condition, color patterns, damage type, disease progression",
  "recommendations": ["5 specific actionable treatment steps"],
  "growth_needs": "specific growing requirements for this crop"
}

Identify the EXACT crop species first. Then check for diseases: blight, scorch, rust, spots, mildew, wilt, rot, nutrient deficiency. Describe damage patterns in detail."""

    # Try vision models — 30s timeout (skip fast if RAM limited)
    for model in ["moondream", "llava"]:
        try:
            logger.info("Trying vision model: %s", model)
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.post(f"{OLLAMA_BASE}/api/generate", json={
                    "model": model,
                    "prompt": prompt,
                    "images": [compressed_b64],
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 400,
                        "num_ctx": 512,
                    },
                })
                r.raise_for_status()
                text = r.json().get("response", "").strip()
                logger.info("Vision/%s raw response: %s", model, text[:200])
                start, end = text.find("{"), text.rfind("}") + 1
                if start >= 0 and end > start:
                    result = json.loads(text[start:end])
                    logger.info("Vision model %s succeeded: crop=%s disease=%s",
                                model, result.get("crop"), result.get("disease"))
                    disease = result.get("disease")
                    if disease and str(disease).lower() in ("null", "none", "n/a", "no", ""):
                        disease = None
                    issues = []
                    if disease:
                        issues.append({"name": disease, "description": result.get("description", "")})
                    return {
                        "crop_detected": result.get("crop", "Unknown"),
                        "severity": result.get("severity", "warning"),
                        "health_assessment": result.get("description", ""),
                        "issues": issues,
                        "recommendations": result.get("recommendations", [])[:5],
                        "growth_needs": result.get("growth_needs", ""),
                        "ai_confidence": 82,
                        "_model": f"ollama-{model}",
                    }
        except httpx.ReadTimeout:
            logger.warning("Vision/%s timed out after 30s", model)
            _vision_failed_count += 1
            continue
        except Exception as e:
            logger.warning("Vision/%s failed: %s", model, str(e)[:120])
            _vision_failed_count += 1
            continue
    return None


async def _get_llm_description(features: dict) -> dict | None:
    """Ask phi3 (or tinyllama fallback) for crop identification + disease diagnosis."""
    import httpx

    green = features["green_pct"]
    brown = features["brown_pct"]
    yellow = features["yellow_pct"]
    necrotic = features.get("necrotic_pct", 0)
    dry_tan = features.get("dry_tan_pct", 0)
    lesion_edge = features.get("lesion_edge_pct", 0)
    orange = features.get("orange_pct", 0)
    red = features.get("red_pct", 0)
    purple = features.get("purple_pct", 0)
    total_damaged = features.get("total_damaged_pct", brown + necrotic + dry_tan)
    spread = features.get("damage_spread_pct", 0)
    spots = features.get("spot_density", 0)
    edge_density = features.get("edge_density", 0)
    avg_r, avg_g, avg_b = features.get("avg_r", 0), features.get("avg_g", 0), features.get("avg_b", 0)
    std_r, std_g, std_b = features.get("std_r", 0), features.get("std_g", 0), features.get("std_b", 0)

    # Build symptom description
    symptoms = []
    if brown > 8: symptoms.append(f"brown/dying tissue: {brown}%")
    if necrotic > 3: symptoms.append(f"dark necrotic dead patches: {necrotic}%")
    if dry_tan > 5: symptoms.append(f"dry papery tan areas: {dry_tan}%")
    if yellow > 8: symptoms.append(f"yellowing (chlorosis): {yellow}%")
    if orange > 3: symptoms.append(f"orange/rust spots: {orange}%")
    if red > 2: symptoms.append(f"red lesions: {red}%")
    if lesion_edge > 3: symptoms.append(f"dark lesion borders: {lesion_edge}%")
    if purple > 5: symptoms.append(f"purple discoloration: {purple}%")
    if spots > 12: symptoms.append(f"many small spots/lesions detected")
    if spread > 30: symptoms.append(f"damage spread across {spread}% of plant")
    if green > 30: symptoms.append(f"remaining healthy green: {green}%")

    symptom_text = "; ".join(symptoms) if symptoms else f"mostly green ({green}%), minimal visible damage"

    prompt = f"""You are an expert agricultural crop pathologist. A farmer sent a crop photo and these are the measured symptoms:

SYMPTOMS: {symptom_text}
COLOR DATA: green={green}%, brown={brown}%, necrotic={necrotic}%, yellow={yellow}%, orange={orange}%, dry_tan={dry_tan}%
TOTAL DAMAGE: {total_damaged}% of plant tissue is damaged

Based on these measurements, answer these 4 questions:
1. CROP: What crop is this most likely? (e.g. Tomato, Potato, Apple, Corn, Rice, Wheat, Mango, Grape, Citrus, Pepper, Bean)
2. DISEASE: What specific disease does it have? (e.g. Late Blight, Leaf Scorch, Bacterial Spot, Anthracnose, Rust, etc.) Say "healthy" if no disease.
3. SEVERITY: Is this critical, warning, or healthy?
4. DESCRIPTION: Describe the condition in 2-3 sentences and give 3-5 treatment recommendations.

Remember: if brown>15% or necrotic>5%, the plant IS diseased."""

    # Try phi3:mini first (best), then tinyllama as fast fallback
    for model in ["phi3:mini", "tinyllama"]:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.post(f"{OLLAMA_BASE}/api/generate", json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 350, "num_ctx": 1024},
                })
                r.raise_for_status()
                text = r.json().get("response", "").strip()
                logger.info("LLM/%s raw: %s", model, text[:200])

                # Try JSON parse first (bonus if model gives structured output)
                start, end = text.find("{"), text.rfind("}") + 1
                if start >= 0 and end > start:
                    try:
                        data = json.loads(text[start:end])
                        crop = data.get("crop", "Unknown")
                        disease = data.get("disease")
                        if disease and str(disease).lower() in ("null", "none", "n/a", "no", ""):
                            disease = None
                        desc = data.get("description", "")
                        recs = data.get("recommendations", [])
                        severity = data.get("severity", "warning")
                        return {
                            "crop": crop if crop else "Unknown",
                            "disease": disease,
                            "description": desc,
                            "severity": severity,
                            "recommendations": recs[:5] if recs else [],
                            "_model": model,
                        }
                    except json.JSONDecodeError:
                        pass  # Fall through to text parsing

                # Text parsing: extract crop, disease, description from prose
                if len(text) > 20:
                    crop = _extract_crop_from_text(text)
                    disease = _extract_disease_from_text(text)
                    severity = None
                    for sev in ["critical", "warning", "healthy"]:
                        if sev in text.lower():
                            severity = sev
                            break

                    # Extract recommendations
                    recs = []
                    for line in text.split("\n"):
                        line = line.strip()
                        if line and (line[0].isdigit() or line.startswith("-") or line.startswith("•")):
                            clean = line.lstrip("0123456789.-•) ").strip()
                            if len(clean) > 15 and any(w in clean.lower() for w in ["apply", "remove", "water", "spray", "prune", "add", "use", "check", "test", "avoid", "ensure", "plant", "rotate", "mulch", "treat"]):
                                recs.append(clean)

                    # Build description from sentences
                    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if len(s.strip()) > 15]
                    description = ". ".join(sentences[:4]) + "." if sentences else text[:300]

                    return {
                        "crop": crop,
                        "disease": disease,
                        "description": description,
                        "severity": severity,
                        "recommendations": recs[:5],
                        "_model": model,
                    }
        except httpx.ReadTimeout:
            logger.info("LLM/%s timed out", model)
            continue
        except json.JSONDecodeError:
            logger.info("LLM/%s returned invalid JSON", model)
            # Still try next model
            continue
        except Exception as e:
            logger.info("LLM/%s failed: %s", model, str(e)[:80])
            continue
    return None


def _extract_disease_from_text(text: str) -> str | None:
    """Extract disease name from freeform LLM text."""
    text_lower = text.lower()
    disease_keywords = {
        "late blight": "Late Blight", "early blight": "Early Blight",
        "leaf scorch": "Leaf Scorch", "leaf blight": "Leaf Blight",
        "apple scab": "Apple Scab", "fire blight": "Fire Blight",
        "black rot": "Black Rot", "anthracnose": "Anthracnose",
        "septoria": "Septoria Leaf Spot", "cercospora": "Cercospora Leaf Spot",
        "alternaria": "Alternaria Blight", "phytophthora": "Phytophthora Blight",
        "powdery mildew": "Powdery Mildew", "downy mildew": "Downy Mildew",
        "bacterial spot": "Bacterial Spot", "bacterial leaf": "Bacterial Leaf Disease",
        "leaf spot": "Leaf Spot Disease", "brown spot": "Brown Spot",
        "rust disease": "Rust Disease", "common rust": "Common Rust",
        "leaf blast": "Leaf Blast", "mosaic virus": "Mosaic Virus",
        "botrytis": "Botrytis (Gray Mold)", "fusarium": "Fusarium Wilt",
        "verticillium": "Verticillium Wilt", "canker": "Canker",
        "scab": "Scab Disease", "rot": "Rot Disease",
        "blight": "Blight", "rust": "Rust Disease",
        "wilt": "Wilt Disease", "necrosis": "Leaf Necrosis",
        "chlorosis": "Chlorosis", "nutrient def": "Nutrient Deficiency",
        "drought": "Drought Stress",
    }
    for keyword, name in disease_keywords.items():
        if keyword in text_lower:
            return name
    return None


def _extract_crop_from_text(text: str) -> str:
    """Extract crop name from freeform LLM text."""
    text_lower = text.lower()
    crops = ["apple", "tomato", "potato", "corn", "maize", "grape", "rice", "wheat",
             "citrus", "orange", "lemon", "mango", "banana", "bean", "soybean",
             "pepper", "cotton", "strawberry", "cherry", "peach", "pear", "plum",
             "cucumber", "squash", "lettuce", "cabbage", "broccoli", "onion",
             "sugarcane", "tea", "coffee"]
    for crop in crops:
        if crop in text_lower:
            return crop.capitalize()
    return "Unknown"


def _identify_crop_from_features(features: dict) -> tuple[str, int]:
    """Identify likely crop from color/texture features. Returns (crop_name, confidence)."""
    green = features.get("green_pct", 0)
    brown = features.get("brown_pct", 0)
    yellow = features.get("yellow_pct", 0)
    dark = features.get("dark_pct", 0)
    avg_r = features.get("avg_r", 0)
    avg_g = features.get("avg_g", 0)
    avg_b = features.get("avg_b", 0)
    std_r = features.get("std_r", 0)
    std_g = features.get("std_g", 0)
    edge_density = features.get("edge_density", 0)
    spots = features.get("spot_density", 0)

    # Score each crop based on color/texture signatures
    scores: dict[str, float] = {}

    # Tomato: broad dark-green leaves, high green, moderate edge detail
    if green > 25 and avg_g > avg_r and avg_g > 70:
        scores["Tomato"] = 20 + (green * 0.2) + (edge_density * 0.5 if edge_density > 15 else 0)
        if avg_g > avg_b * 1.3:
            scores["Tomato"] += 8

    # Apple: bright green leaves, smoother texture, often lighter green
    if green > 20 and avg_g > 80 and edge_density < 25:
        scores["Apple"] = 18 + (green * 0.15)
        if avg_r > 60 and avg_r < 120:
            scores["Apple"] += 5

    # Grape: darker green, sometimes purple tints, lobed leaves
    if green > 20:
        scores["Grape"] = 12 + (green * 0.1)
        if features.get("purple_pct", 0) > 2:
            scores["Grape"] += 15
        if avg_g > 60 and avg_b > 40:
            scores["Grape"] += 5

    # Potato: medium green, compound leaves, similar to tomato
    if green > 20 and avg_g > 60:
        scores["Potato"] = 15 + (green * 0.15)
        if yellow > 5:
            scores["Potato"] += 3

    # Corn/Maize: very elongated, uniform green, less texture variation
    if green > 30 and std_r < 40 and std_g < 45:
        scores["Corn"] = 15 + (green * 0.2)
        if edge_density < 15:  # Smooth long leaves
            scores["Corn"] += 10

    # Rice: very narrow, uniform, lighter green
    if green > 25 and avg_g > 90 and std_g < 35:
        scores["Rice"] = 12 + (green * 0.15)
        if edge_density < 12:
            scores["Rice"] += 8

    # Wheat: yellow-green to golden, narrow leaves
    if green > 10 and yellow > 10:
        scores["Wheat"] = 10 + (yellow * 0.3)
        if avg_r > avg_g and avg_g > 80:
            scores["Wheat"] += 8

    # Citrus: glossy dark-green, thick leaves
    if green > 30 and avg_g > 70 and dark < 20:
        scores["Citrus"] = 14 + (green * 0.15)
        if avg_b < 60 and avg_g > avg_r:
            scores["Citrus"] += 5

    # Pepper: dark green, smooth, broad
    if green > 25 and avg_g > 60 and dark > 8:
        scores["Pepper"] = 12 + (green * 0.1)

    # Mango: large broad leaves, dark green
    if green > 30 and avg_g > 70 and edge_density < 20:
        scores["Mango"] = 14 + (green * 0.1)
        if avg_r < 80 and avg_g > 90:
            scores["Mango"] += 5

    if not scores:
        return "Unknown", 0

    best_crop = max(scores, key=scores.get)
    best_score = scores[best_crop]
    # Second best for confidence gap
    sorted_crops = sorted(scores.values(), reverse=True)
    gap = sorted_crops[0] - sorted_crops[1] if len(sorted_crops) > 1 else sorted_crops[0]

    confidence = min(int(best_score + gap * 0.5), 70)
    return best_crop, confidence


def _build_pil_result(features: dict) -> dict:
    """Build comprehensive analysis from PIL image features — checks ALL damage indicators, not just greenness."""
    green = features["green_pct"]
    brown = features["brown_pct"]
    yellow = features["yellow_pct"]
    dark = features["dark_pct"]
    necrotic = features.get("necrotic_pct", 0)
    dry_tan = features.get("dry_tan_pct", 0)
    lesion_edge = features.get("lesion_edge_pct", 0)
    orange = features.get("orange_pct", 0)
    red = features.get("red_pct", 0)
    purple = features.get("purple_pct", 0)
    total_damaged = features.get("total_damaged_pct", 0)
    spread = features.get("damage_spread_pct", 0)
    spots = features.get("spot_density", 0)

    issues = []
    severity_score = 0  # Accumulate damage evidence

    # ── Check EVERY damage indicator (not just green %) ───────────────
    if brown > 15:
        issues.append({
            "name": "Brown Tissue / Leaf Blight",
            "description": f"Significant brown/dying tissue ({brown}%). Indicates possible blight, bacterial infection, or severe drought stress. Leaf edges and tips are often affected first."
        })
        severity_score += min(brown, 40)

    if necrotic > 5:
        issues.append({
            "name": "Necrotic Lesions (Dead Tissue)",
            "description": f"Dark necrotic patches ({necrotic}%) — dead plant cells. Common in advanced fungal/bacterial infections. Tissue cannot recover."
        })
        severity_score += necrotic * 2

    if dry_tan > 10:
        issues.append({
            "name": "Dry / Papery Leaf Damage",
            "description": f"Dry tan areas ({dry_tan}%) show desiccated tissue — could be sunscorch, drought stress, or late-stage blight."
        })
        severity_score += dry_tan * 1.5

    if yellow > 15:
        issues.append({
            "name": "Chlorosis (Yellowing)",
            "description": f"Yellowing at {yellow}%. May indicate nitrogen/iron deficiency, overwatering, root damage, or early-stage disease."
        })
        severity_score += yellow * 0.8

    if orange > 5:
        issues.append({
            "name": "Rust Disease Indicator",
            "description": f"Orange/rust colored areas ({orange}%) — typical of rust fungal diseases (Puccinia spp.). Pustules release spores and spread rapidly."
        })
        severity_score += orange * 2

    if red > 3:
        issues.append({
            "name": "Red Spots / Lesions",
            "description": f"Red spots ({red}%) could indicate bacterial leaf spot, anthracnose, or viral infection."
        })
        severity_score += red * 2

    if lesion_edge > 5:
        issues.append({
            "name": "Distinct Lesion Borders",
            "description": f"Dark borders around damaged areas ({lesion_edge}%) are characteristic of fungal leaf spots (Septoria, Cercospora)."
        })
        severity_score += lesion_edge * 1.5

    if spots > 20 and total_damaged > 10:
        issues.append({
            "name": "High Spot / Lesion Density",
            "description": f"Texture analysis shows many distinct spots/lesions ({spots}% density). Multiple infection points spread across the leaf."
        })
        severity_score += 10

    if purple > 8:
        issues.append({
            "name": "Purple Discoloration",
            "description": f"Purple coloring ({purple}%) may indicate phosphorus deficiency or cold stress."
        })
        severity_score += purple

    if dark > 10:
        issues.append({
            "name": "Dark Spots / Severe Damage",
            "description": f"Very dark areas ({dark}%) suggest severe necrosis, sooty mold, or advanced disease."
        })
        severity_score += dark * 1.5

    # ── Determine overall severity ─────────────────────────────────────
    # Key insight: check damage FIRST, then greenness.
    # A plant with 50% green CAN still be severely diseased if 30%+ is brown/necrotic.

    if severity_score >= 40 or total_damaged > 35:
        severity = "critical"
        health_status = "severely diseased"
    elif severity_score >= 20 or total_damaged > 20:
        severity = "warning"
        health_status = "moderately damaged"
    elif severity_score >= 8 or total_damaged > 10:
        severity = "warning"
        health_status = "showing early damage"
    elif green > 50 and total_damaged < 5 and not issues:
        severity = "healthy"
        health_status = "healthy"
    elif green > 30 and total_damaged < 8 and len(issues) <= 1:
        severity = "healthy"
        health_status = "mostly healthy with minor concerns"
    else:
        severity = "warning"
        health_status = "needs attention"

    # ── Build description ──────────────────────────────────────────────
    if issues:
        issue_names = [i["name"].split(" /")[0].split(" (")[0] for i in issues[:3]]
        desc = f"Plant is {health_status}. Detected: {', '.join(issue_names)}. "
        desc += f"Healthy tissue: {green}%, Damaged tissue: {total_damaged}%. "
        if spread > 40:
            desc += f"Damage is widespread, affecting {spread}% of the plant area."
        elif spread > 20:
            desc += f"Damage is spreading — currently in {spread}% of the plant area."
        else:
            desc += "Damage is localized to specific areas."
    else:
        desc = f"Plant appears {health_status} with {green}% green tissue and active photosynthesis. "
        desc += "No significant disease indicators detected."

    # Select knowledge base
    knowledge = GENERIC_KNOWLEDGE["diseased"] if issues else GENERIC_KNOWLEDGE["healthy"]

    # Build tailored recommendations based on what we found
    custom_recs = []
    if brown > 15 or necrotic > 5:
        custom_recs.extend([
            "Remove severely damaged leaves to prevent disease spread to healthy tissue.",
            "Apply copper-based fungicide (Bordeaux mixture) as immediate treatment.",
            "Check for adequate drainage — waterlogged roots worsen leaf blight.",
        ])
    if yellow > 15:
        custom_recs.extend([
            "Test soil for nitrogen and iron levels — chlorosis often indicates deficiency.",
            "Apply balanced fertilizer (10-10-10) or chelated iron supplement.",
        ])
    if orange > 5:
        custom_recs.extend([
            "Apply triazole fungicide to treat rust disease.",
            "Improve air circulation — prune dense growth.",
        ])
    if dry_tan > 10:
        custom_recs.extend([
            "Check irrigation schedule — drought stress causes papery leaf damage.",
            "Apply mulch to retain soil moisture.",
        ])
    if spread > 50:
        custom_recs.append("URGENT: Damage is widespread. Consult local agricultural extension office immediately.")

    # Merge custom recs with generic ones, dedup
    if custom_recs:
        final_recs = custom_recs[:5]
        for rec in knowledge["recommendations"]:
            if len(final_recs) >= 6:
                break
            if rec not in final_recs:
                final_recs.append(rec)
    else:
        final_recs = knowledge["recommendations"]

    # Calculate confidence based on how much data we have
    confidence = 30
    if total_damaged > 15:
        confidence = 45  # More confident about disease when damage is clear
    if spots > 15:
        confidence += 5
    if len(issues) >= 2:
        confidence += 5

    return {
        "crop_detected": _identify_crop_from_features(features)[0],
        "severity": severity,
        "health_assessment": desc,
        "issues": issues,
        "recommendations": final_recs,
        "growth_needs": knowledge["growth_needs"],
        "ai_confidence": min(confidence, 60),
        "_model": "pil-advanced",
        "_color_stats": {
            "green_pct": green, "brown_pct": brown,
            "yellow_pct": yellow, "necrotic_pct": necrotic,
            "dry_tan_pct": dry_tan, "damaged_total_pct": total_damaged,
            "spread_pct": spread,
        },
    }


# ── Main Entry Point ─────────────────────────────────────────────────────

async def analyze_crop_image(image_base64: str) -> dict:
    """
    Analyze a crop image — completely free, no API keys.
    Pipeline: vision LLM → PIL + text LLM → PIL-only → knowledge base.
    """
    image_bytes = base64.b64decode(image_base64)
    features = extract_image_features(image_bytes)

    # 1. Try vision models (best quality, needs RAM)
    result = await _try_vision_models(image_base64)
    if result:
        _enrich_from_knowledge_base(result)
        return result

    # 2. Build PIL result + enhance with text LLM description
    result = _build_pil_result(features)
    llm_result = await _get_llm_description(features)
    if llm_result:
        # LLM now returns structured data: crop, disease, severity, recommendations
        model_used = llm_result.get("_model", "phi3")
        result["_model"] = f"pil-advanced+{model_used}"

        # Use LLM crop identification (overrides PIL guess if not Unknown)
        llm_crop = llm_result.get("crop", "Unknown")
        if llm_crop and llm_crop != "Unknown":
            result["crop_detected"] = llm_crop
            result["ai_confidence"] = min(result["ai_confidence"] + 20, 75)
        else:
            result["ai_confidence"] = min(result["ai_confidence"] + 10, 65)

        # Use LLM description if available
        if llm_result.get("description"):
            result["health_assessment"] = llm_result["description"]

        # Use LLM severity if it disagrees and LLM thinks worse
        llm_severity = llm_result.get("severity")
        severity_rank = {"healthy": 0, "warning": 1, "critical": 2}
        if llm_severity and severity_rank.get(llm_severity, 0) > severity_rank.get(result["severity"], 0):
            result["severity"] = llm_severity

        # Use LLM recommendations if provided
        if llm_result.get("recommendations"):
            result["recommendations"] = llm_result["recommendations"]

        # Add LLM-detected disease to issues
        if llm_result.get("disease"):
            disease_name = llm_result["disease"]
            existing_names = [i["name"] for i in result.get("issues", [])]
            if disease_name not in existing_names:
                result["issues"].insert(0, {
                    "name": disease_name,
                    "description": f"AI identified {disease_name} from symptom pattern analysis."
                })

    _enrich_from_knowledge_base(result)
    return result


def _enrich_from_knowledge_base(result: dict) -> None:
    """Cross-reference with disease knowledge base for expert recommendations."""
    crop = result.get("crop_detected", "").lower()
    severity = result.get("severity", "")
    issues = result.get("issues", [])
    issues_text = " ".join(str(i) for i in issues).lower()
    health_text = result.get("health_assessment", "").lower()
    all_text = issues_text + " " + health_text

    # 1. Try crop-specific match first
    for key, knowledge in DISEASE_KNOWLEDGE.items():
        if knowledge["crop"].lower() in crop and knowledge["crop"] != "General":
            if knowledge["disease"] is None and severity == "healthy":
                result["recommendations"] = knowledge["recommendations"]
                result["growth_needs"] = knowledge["growth_needs"]
                return
            if knowledge["disease"] and any(
                knowledge["disease"].lower() in str(i).lower()
                for i in issues
            ):
                result["recommendations"] = knowledge["recommendations"]
                result["growth_needs"] = knowledge["growth_needs"]
                return

    # 2. Try matching general disease patterns by symptoms
    disease_symptom_map = {
        "General___Leaf_scorch": ["scorch", "leaf edge", "margin brown", "papery", "dried edge"],
        "General___Leaf_blight": ["blight", "brown patch", "necrotic", "dead tissue", "leaf blight", "brown tissue"],
        "General___Anthracnose": ["anthracnose", "sunken lesion", "dark lesion"],
        "General___Septoria_leaf_spot": ["septoria", "leaf spot", "gray center", "pycnidia"],
        "General___Cercospora_leaf_spot": ["cercospora", "circular spot", "purple border"],
        "General___Nutrient_deficiency": ["nutrient", "deficiency", "chlorosis", "nitrogen", "iron"],
        "General___Drought_stress": ["drought", "wilt", "curling", "dry stress"],
        "General___Powdery_mildew": ["powdery mildew", "white powder", "powdery", "mildew"],
        "General___Rust": ["rust", "pustule", "orange spot", "rust disease"],
    }

    for key, keywords in disease_symptom_map.items():
        if any(kw in all_text for kw in keywords):
            knowledge = DISEASE_KNOWLEDGE[key]
            result["recommendations"] = knowledge["recommendations"]
            result["growth_needs"] = knowledge["growth_needs"]
            return

    # 3. Auto-match by damage pattern when no specific disease found
    if severity in ("critical", "warning") and issues:
        brown_issues = any("brown" in str(i).lower() or "blight" in str(i).lower() or "necrotic" in str(i).lower() for i in issues)
        if brown_issues and "General___Leaf_blight" in DISEASE_KNOWLEDGE:
            knowledge = DISEASE_KNOWLEDGE["General___Leaf_blight"]
            result["recommendations"] = knowledge["recommendations"]
            result["growth_needs"] = knowledge["growth_needs"]
            return
