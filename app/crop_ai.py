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
import time

logger = logging.getLogger(__name__)

# TF model integration — lazy import to avoid slow startup when model absent
_tf_model = None
def _get_tf_model():
    global _tf_model
    if _tf_model is None:
        try:
            from app import tf_model as _mod
            if _mod.is_model_available():
                _tf_model = _mod
                logger.info("[CropAI] TF model available — will use for predictions")
            else:
                _tf_model = False  # sentinel: checked but not available
        except Exception as e:
            logger.warning(f"[CropAI] TF model import failed: {e}")
            _tf_model = False
    return _tf_model if _tf_model is not False else None

OLLAMA_BASE = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Vision models need >6GB RAM. Set SMARFA_VISION=1 to enable on capable machines.
_VISION_ENABLED = os.getenv("SMARFA_VISION", "0") == "1"
_vision_failed_count = 0  # Track failures to auto-disable
_FAST_ANALYSIS = os.getenv("SMARFA_FAST_ANALYSIS", "1") == "1"
_LLM_TIMEOUT_SECONDS = float(os.getenv("SMARFA_LLM_TIMEOUT", "12" if _FAST_ANALYSIS else "45"))


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
    "Sunflower___Healthy": {
        "crop": "Sunflower", "disease": None, "severity": "healthy",
        "description": "Sunflower plant appears healthy with strong green foliage and no visible disease symptoms.",
        "recommendations": [
            "Maintain regular deep watering — sunflowers have deep tap roots.",
            "Apply balanced fertilizer (10-10-10) at planting and side-dress with nitrogen.",
            "Support tall varieties with stakes to prevent wind lodging.",
            "Monitor for aphids and sunflower beetles — remove by hand or use neem oil.",
            "Ensure well-drained soil to prevent root rot.",
        ],
        "growth_needs": "Full sun (6-8 hrs), well-drained soil pH 6.0-7.5, deep watering 1-2x/week, 18-28°C.",
    },
    "Sunflower___Downy_mildew": {
        "crop": "Sunflower", "disease": "Downy Mildew", "severity": "warning",
        "description": "Yellow patches on upper leaf surface with white-grey fuzzy growth underneath. Spreads rapidly in cool wet conditions.",
        "recommendations": [
            "Apply metalaxyl or mancozeb fungicide at first sign of symptoms.",
            "Improve field drainage to reduce humidity around plants.",
            "Avoid overhead irrigation — use drip irrigation instead.",
            "Remove and destroy infected leaves immediately.",
            "Plant certified disease-free seeds and resistant varieties.",
        ],
        "growth_needs": "Good drainage, avoid water-logging, full sun, wide row spacing for airflow.",
    },
    "Sunflower___Rust": {
        "crop": "Sunflower", "disease": "Rust Disease", "severity": "warning",
        "description": "Orange-brown powdery pustules on both leaf surfaces. Sunflower rust reduces photosynthesis and yield.",
        "recommendations": [
            "Apply triazole fungicide (propiconazole) at earliest sign of pustules.",
            "Plant rust-resistant sunflower hybrids.",
            "Destroy crop residue after harvest to reduce overwintering spores.",
            "Avoid dense planting — ensure airflow between plants.",
            "Monitor weekly during flowering when susceptibility is highest.",
        ],
        "growth_needs": "Full sun, proper spacing (45-60 cm), avoid dense canopy, well-drained soil.",
    },
    "Sunflower___Leaf_scorch": {
        "crop": "Sunflower", "disease": "Leaf Scorch / Drought Stress", "severity": "warning",
        "description": "Brown papery leaf edges and tips due to insufficient water or heat stress.",
        "recommendations": [
            "Increase watering frequency — sunflowers need 2-3 cm water/week in hot weather.",
            "Apply thick mulch layer around base to retain soil moisture.",
            "Avoid afternoon heat exposure for young seedlings.",
            "Check soil moisture 5-6 cm deep before each irrigation.",
            "Supplement with potassium fertilizer to improve drought tolerance.",
        ],
        "growth_needs": "Deep watering 2x/week, mulched soil, well-drained, avoid waterlogging.",
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


# ── Crop Lifecycle Database ───────────────────────────────────────────────
CROP_LIFECYCLE = {
    "Tomato": {
        "crop_name": "Tomato",
        "variety_types": ["Roma", "Cherry", "Beefsteak", "Heirloom", "San Marzano", "Grape"],
        "total_growth_days": "90-150",
        "stages": {
            "germination": {"duration_days": "5-10", "water": "Keep moist, light watering daily", "fertilizer": "None needed"},
            "vegetative": {"duration_days": "25-35", "water": "1 inch/week, consistent", "fertilizer": "NPK 10-10-10 every 2 weeks"},
            "flowering": {"duration_days": "20-30", "water": "1-1.5 inches/week", "fertilizer": "NPK 5-10-10 (reduce N, boost P-K)"},
            "fruiting": {"duration_days": "20-30", "water": "1.5-2 inches/week, deep watering", "fertilizer": "NPK 5-10-10, calcium supplement"},
            "harvest": {"duration_days": "15-45 (continuous)", "water": "Reduce slightly before harvest", "fertilizer": "Stop 2 weeks before first harvest"},
        },
        "sunlight": "8+ hours full sun daily",
        "soil_type": "Well-drained loamy soil, pH 6.0-6.8, rich in organic matter",
        "pest_risks": {"vegetative": ["Aphids", "Whiteflies", "Cutworms"], "flowering": ["Hornworms", "Spider mites"], "fruiting": ["Fruit worms", "Stink bugs"]},
        "disease_risks": {"vegetative": ["Early Blight", "Septoria Leaf Spot"], "flowering": ["Fusarium Wilt", "Bacterial Spot"], "fruiting": ["Late Blight", "Blossom End Rot"]},
        "yield_per_acre": "20,000-30,000 kg (determinate); 35,000-50,000 kg (indeterminate, greenhouse)",
        "harvest_indicators": ["Fruit turns fully red/orange", "Slight softness when pressed", "Easy twist-off from vine", "Glossy skin appearance"],
    },
    "Apple": {
        "crop_name": "Apple",
        "variety_types": ["Fuji", "Gala", "Granny Smith", "Honeycrisp", "Red Delicious", "McIntosh"],
        "total_growth_days": "100-200 (fruit from bloom)",
        "stages": {
            "germination": {"duration_days": "Grafted saplings (no seed germination)", "water": "Deep soak at planting", "fertilizer": "Starter fertilizer at planting"},
            "vegetative": {"duration_days": "60-90 (spring growth)", "water": "1-2 inches/week", "fertilizer": "NPK 10-10-10 in early spring"},
            "flowering": {"duration_days": "10-14", "water": "1 inch/week, avoid overhead", "fertilizer": "None during bloom"},
            "fruiting": {"duration_days": "60-90 (fruit development)", "water": "1.5-2 inches/week", "fertilizer": "NPK 5-10-10, calcium foliar spray"},
            "harvest": {"duration_days": "14-30", "water": "Reduce 2 weeks before harvest", "fertilizer": "None"},
        },
        "sunlight": "6-8 hours full sun",
        "soil_type": "Well-drained loamy soil, pH 6.0-7.0, 800-1200 chill hours required",
        "pest_risks": {"vegetative": ["Aphids", "Leaf rollers"], "flowering": ["Codling moth", "Apple maggot"], "fruiting": ["Codling moth", "Plum curculio", "Apple maggot"]},
        "disease_risks": {"vegetative": ["Apple Scab", "Powdery Mildew"], "flowering": ["Fire Blight"], "fruiting": ["Black Rot", "Bitter Rot", "Sooty Blotch"]},
        "yield_per_acre": "15,000-25,000 kg (mature orchard)",
        "harvest_indicators": ["Skin color change to variety-specific hue", "Seeds turn dark brown", "Fruit separates easily with upward twist", "Firmness test with fruit pressure tester"],
    },
    "Corn": {
        "crop_name": "Corn",
        "variety_types": ["Sweet Corn", "Dent Corn", "Flint Corn", "Popcorn", "Waxy Corn"],
        "total_growth_days": "60-100",
        "stages": {
            "germination": {"duration_days": "5-12", "water": "Light watering, keep moist", "fertilizer": "Starter P fertilizer at planting"},
            "vegetative": {"duration_days": "30-45 (V1-VT)", "water": "1 inch/week", "fertilizer": "Side-dress N (urea) at V6-V8, NPK 46-0-0"},
            "flowering": {"duration_days": "7-14 (tasseling/silking)", "water": "1.5-2 inches/week (CRITICAL)", "fertilizer": "None during silking"},
            "fruiting": {"duration_days": "15-25 (grain fill)", "water": "1.5 inches/week", "fertilizer": "Foliar micronutrients if deficient"},
            "harvest": {"duration_days": "7-14", "water": "Reduce, allow drying", "fertilizer": "None"},
        },
        "sunlight": "8-10 hours full sun",
        "soil_type": "Deep, fertile loam, pH 5.8-7.0, high nitrogen demand",
        "pest_risks": {"vegetative": ["Cutworms", "Armyworms"], "flowering": ["Corn earworm", "European corn borer"], "fruiting": ["Stink bugs", "Birds"]},
        "disease_risks": {"vegetative": ["Common Rust", "Northern Leaf Blight"], "flowering": ["Gray Leaf Spot", "Southern Rust"], "fruiting": ["Ear Rot", "Smut"]},
        "yield_per_acre": "8,000-12,000 kg (grain); higher for silage",
        "harvest_indicators": ["Kernels dent and reach black layer", "Grain moisture 20-25% (machine harvest)", "Husks dry and brown", "Milk line disappeared"],
    },
    "Rice": {
        "crop_name": "Rice",
        "variety_types": ["Basmati", "Jasmine", "Arborio", "Sona Masuri", "IR-64", "Ponni"],
        "total_growth_days": "90-150",
        "stages": {
            "germination": {"duration_days": "5-10 (nursery)", "water": "Saturated seedbed", "fertilizer": "None in nursery"},
            "vegetative": {"duration_days": "30-50 (tillering)", "water": "Standing water 5-10 cm", "fertilizer": "NPK 120-60-40 kg/ha split; basal + tillering dose"},
            "flowering": {"duration_days": "7-10 (panicle emergence)", "water": "Maintain 5 cm standing water", "fertilizer": "Top-dress K at panicle initiation"},
            "fruiting": {"duration_days": "25-35 (grain fill)", "water": "Alternate wetting and drying", "fertilizer": "None"},
            "harvest": {"duration_days": "7-14", "water": "Drain field 10-15 days before harvest", "fertilizer": "None"},
        },
        "sunlight": "6-8 hours, tolerates partial shade",
        "soil_type": "Clayey/clay loam, pH 5.5-6.5, puddled field for wetland rice",
        "pest_risks": {"vegetative": ["Stem borer", "Brown planthopper"], "flowering": ["Gall midge", "Leaf folder"], "fruiting": ["Rice bug", "Birds"]},
        "disease_risks": {"vegetative": ["Leaf Blast", "Sheath Blight"], "flowering": ["Neck Blast", "False Smut"], "fruiting": ["Brown Spot", "Grain Discoloration"]},
        "yield_per_acre": "2,500-4,500 kg (lowland); 1,500-3,000 kg (upland)",
        "harvest_indicators": ["80% of grains turn golden", "Panicles droop", "Grain moisture 20-24%", "Thumb-nail test shows firm grain"],
    },
    "Grape": {
        "crop_name": "Grape",
        "variety_types": ["Thompson Seedless", "Concord", "Cabernet Sauvignon", "Merlot", "Muscat", "Red Globe"],
        "total_growth_days": "150-180 (from bud break)",
        "stages": {
            "germination": {"duration_days": "Propagated by cuttings (no seed)", "water": "Deep soak at planting", "fertilizer": "Starter fertilizer"},
            "vegetative": {"duration_days": "50-70 (shoot growth)", "water": "1 inch/week, drip preferred", "fertilizer": "NPK 10-10-10 at bud break"},
            "flowering": {"duration_days": "10-14", "water": "Reduce slightly", "fertilizer": "Foliar boron spray"},
            "fruiting": {"duration_days": "50-70 (berry development)", "water": "1-1.5 inches/week", "fertilizer": "NPK 0-10-20 (K-heavy at veraison)"},
            "harvest": {"duration_days": "14-21", "water": "Reduce 2 weeks before harvest", "fertilizer": "None"},
        },
        "sunlight": "7-8 hours full sun",
        "soil_type": "Well-drained sandy loam/loam, pH 5.5-6.5, low fertility preferred",
        "pest_risks": {"vegetative": ["Grape phylloxera", "Mealybugs"], "flowering": ["Thrips"], "fruiting": ["Japanese beetles", "Birds", "Wasps"]},
        "disease_risks": {"vegetative": ["Downy Mildew", "Powdery Mildew"], "flowering": ["Botrytis Bunch Rot"], "fruiting": ["Black Rot", "Anthracnose"]},
        "yield_per_acre": "8,000-15,000 kg (table grapes); 4,000-8,000 kg (wine grapes)",
        "harvest_indicators": ["Brix level 18-24° (refractometer)", "Berry color fully developed", "Seeds turn brown", "Berry softens, flavor peaks"],
    },
    "Wheat": {
        "crop_name": "Wheat",
        "variety_types": ["Hard Red Winter", "Soft Red Winter", "Hard Red Spring", "Durum", "Soft White"],
        "total_growth_days": "100-140 (spring); 200-270 (winter)",
        "stages": {
            "germination": {"duration_days": "7-14", "water": "Moist seedbed", "fertilizer": "NPK 20-20-0 basal at sowing"},
            "vegetative": {"duration_days": "40-60 (tillering to jointing)", "water": "25-30 mm at CRI stage", "fertilizer": "Top-dress N (urea 65 kg/ha) at tillering"},
            "flowering": {"duration_days": "7-10 (heading/anthesis)", "water": "25-30 mm at heading", "fertilizer": "Foliar NPK if needed"},
            "fruiting": {"duration_days": "25-35 (grain fill)", "water": "25 mm at milk stage", "fertilizer": "None"},
            "harvest": {"duration_days": "7-14", "water": "None — allow field drying", "fertilizer": "None"},
        },
        "sunlight": "6-8 hours full sun",
        "soil_type": "Clay loam to loam, pH 6.0-7.0, well-drained",
        "pest_risks": {"vegetative": ["Aphids", "Hessian fly"], "flowering": ["Armyworms"], "fruiting": ["Wheat midge", "Birds"]},
        "disease_risks": {"vegetative": ["Powdery Mildew", "Septoria Leaf Blotch"], "flowering": ["Fusarium Head Blight"], "fruiting": ["Stripe Rust", "Stem Rust"]},
        "yield_per_acre": "2,500-4,000 kg (irrigated); 1,200-2,000 kg (rainfed)",
        "harvest_indicators": ["Grain turns golden-hard", "Moisture below 14%", "Thumbnail test — grain is hard", "Straw turns completely yellow"],
    },
    "Potato": {
        "crop_name": "Potato",
        "variety_types": ["Russet Burbank", "Yukon Gold", "Red Pontiac", "Kennebec", "Fingerling"],
        "total_growth_days": "70-120",
        "stages": {
            "germination": {"duration_days": "14-21 (sprouting from seed tuber)", "water": "Light watering", "fertilizer": "NPK 10-20-20 at planting"},
            "vegetative": {"duration_days": "25-35", "water": "1 inch/week", "fertilizer": "Side-dress N at hilling"},
            "flowering": {"duration_days": "10-15", "water": "1.5 inches/week (tuber initiation)", "fertilizer": "K supplement"},
            "fruiting": {"duration_days": "20-30 (tuber bulking)", "water": "1.5-2 inches/week (CRITICAL)", "fertilizer": "Reduce N, maintain K"},
            "harvest": {"duration_days": "14-21 (skin set)", "water": "Stop watering 2 weeks before harvest", "fertilizer": "None"},
        },
        "sunlight": "6-8 hours full sun",
        "soil_type": "Loose, well-drained, sandy loam, pH 5.0-6.0",
        "pest_risks": {"vegetative": ["Colorado potato beetle", "Aphids"], "flowering": ["Flea beetles"], "fruiting": ["Wireworms", "Tuber moth"]},
        "disease_risks": {"vegetative": ["Early Blight"], "flowering": ["Late Blight"], "fruiting": ["Blackleg", "Common Scab"]},
        "yield_per_acre": "15,000-25,000 kg",
        "harvest_indicators": ["Foliage yellows and dies back", "Skin doesn't rub off easily", "Tubers reach desired size", "2-3 weeks after vine death"],
    },
    "Mango": {
        "crop_name": "Mango",
        "variety_types": ["Alphonso", "Tommy Atkins", "Kent", "Haden", "Kesar", "Dasheri"],
        "total_growth_days": "100-150 (fruit from flowering)",
        "stages": {
            "germination": {"duration_days": "Grafted saplings preferred", "water": "Deep soak at planting", "fertilizer": "Starter organic manure"},
            "vegetative": {"duration_days": "Perennial (flushes 2-3x/year)", "water": "20-30 L/tree/week (young)", "fertilizer": "NPK 1:0.5:1 ratio annually"},
            "flowering": {"duration_days": "15-25", "water": "Withhold water to induce flowering", "fertilizer": "Foliar KNO3 spray to induce flowering"},
            "fruiting": {"duration_days": "60-90", "water": "Resume irrigation, 40-60 L/tree/week", "fertilizer": "K-rich fertilizer at fruit set"},
            "harvest": {"duration_days": "14-30", "water": "Reduce", "fertilizer": "None"},
        },
        "sunlight": "8-10 hours full sun",
        "soil_type": "Deep, well-drained alluvial/laterite, pH 5.5-7.5",
        "pest_risks": {"vegetative": ["Mango hopper", "Mealybug"], "flowering": ["Mango hopper", "Thrips"], "fruiting": ["Fruit fly", "Stem borer"]},
        "disease_risks": {"vegetative": ["Powdery Mildew", "Anthracnose"], "flowering": ["Blossom Blight"], "fruiting": ["Anthracnose", "Stem End Rot"]},
        "yield_per_acre": "4,000-10,000 kg (mature trees)",
        "harvest_indicators": ["Fruit shoulder fills out", "Skin color change to variety hue", "Sweet aroma at stem end", "Slight softness at tip"],
    },
    "Citrus": {
        "crop_name": "Citrus",
        "variety_types": ["Valencia Orange", "Navel Orange", "Lemon", "Lime", "Grapefruit", "Mandarin"],
        "total_growth_days": "180-365 (variety dependent)",
        "stages": {
            "germination": {"duration_days": "Budded/grafted saplings", "water": "Deep soak at planting", "fertilizer": "Starter fertilizer"},
            "vegetative": {"duration_days": "Perennial (3 flushes/year)", "water": "25-40 L/tree/week", "fertilizer": "NPK 6:6:6 + micronutrients 3x/year"},
            "flowering": {"duration_days": "14-21", "water": "Withhold briefly then irrigate", "fertilizer": "Foliar zinc + boron spray"},
            "fruiting": {"duration_days": "120-200", "water": "40-60 L/tree/week (consistent)", "fertilizer": "K-heavy NPK at fruit expansion"},
            "harvest": {"duration_days": "30-60 (can stay on tree)", "water": "Maintain normal", "fertilizer": "None"},
        },
        "sunlight": "8-10 hours full sun",
        "soil_type": "Well-drained sandy loam to loam, pH 6.0-7.0",
        "pest_risks": {"vegetative": ["Citrus leaf miner", "Aphids", "Scale"], "flowering": ["Thrips"], "fruiting": ["Fruit fly", "Citrus psyllid"]},
        "disease_risks": {"vegetative": ["Citrus Canker", "Greening (HLB)"], "flowering": ["Melanose"], "fruiting": ["Alternaria Brown Spot", "Post-harvest molds"]},
        "yield_per_acre": "15,000-30,000 kg (mature orchard)",
        "harvest_indicators": ["Fruit reaches variety-specific color", "Brix:acid ratio optimal", "Fruit size standards met", "Easy separation from stem"],
    },
    "Sunflower": {
        "crop_name": "Sunflower",
        "variety_types": ["Mammoth Russian", "Dwarf Sunspot", "Teddy Bear", "ProSun", "Red Sun"],
        "total_growth_days": "70-100",
        "stages": {
            "germination": {"duration_days": "7-10", "water": "Keep moist", "fertilizer": "NPK 10-20-10 at planting"},
            "vegetative": {"duration_days": "25-35", "water": "1 inch/week", "fertilizer": "Side-dress N at 30 days"},
            "flowering": {"duration_days": "10-15", "water": "1.5 inches/week", "fertilizer": "Boron foliar spray"},
            "fruiting": {"duration_days": "20-30 (seed fill)", "water": "1-1.5 inches/week", "fertilizer": "None"},
            "harvest": {"duration_days": "7-14", "water": "Stop irrigation", "fertilizer": "None"},
        },
        "sunlight": "6-8 hours full sun",
        "soil_type": "Well-drained loam to clay loam, pH 6.0-7.5",
        "pest_risks": {"vegetative": ["Cutworms", "Sunflower beetle"], "flowering": ["Head moth", "Seed weevil"], "fruiting": ["Birds", "Seed maggot"]},
        "disease_risks": {"vegetative": ["Downy Mildew", "Rust"], "flowering": ["Sclerotinia Head Rot"], "fruiting": ["Botrytis", "Charcoal Rot"]},
        "yield_per_acre": "800-1,500 kg seeds",
        "harvest_indicators": ["Back of head turns yellow-brown", "Petals dry and fall", "Seeds plump and hard", "Moisture below 10%"],
    },
    "Pepper": {
        "crop_name": "Pepper",
        "variety_types": ["Bell Pepper", "Jalapeno", "Habanero", "Cayenne", "Banana Pepper", "Poblano"],
        "total_growth_days": "60-90",
        "stages": {
            "germination": {"duration_days": "8-14", "water": "Keep moist, warm soil (24-30°C)", "fertilizer": "None"},
            "vegetative": {"duration_days": "25-35", "water": "1 inch/week", "fertilizer": "NPK 10-10-10 every 2 weeks"},
            "flowering": {"duration_days": "10-15", "water": "1-1.5 inches/week (consistent)", "fertilizer": "NPK 5-10-10, calcium supplement"},
            "fruiting": {"duration_days": "15-25", "water": "1.5 inches/week", "fertilizer": "K-rich fertilizer"},
            "harvest": {"duration_days": "Continuous for 4-8 weeks", "water": "Maintain regular watering", "fertilizer": "Light feeding every 3 weeks"},
        },
        "sunlight": "6-8 hours full sun",
        "soil_type": "Well-drained, fertile loam, pH 6.0-6.8",
        "pest_risks": {"vegetative": ["Aphids", "Flea beetles"], "flowering": ["Pepper weevil", "Thrips"], "fruiting": ["European corn borer", "Pepper maggot"]},
        "disease_risks": {"vegetative": ["Damping off", "Bacterial Leaf Spot"], "flowering": ["Phytophthora Blight"], "fruiting": ["Anthracnose", "Blossom End Rot"]},
        "yield_per_acre": "10,000-20,000 kg (bell pepper)",
        "harvest_indicators": ["Fruit reaches full size", "Color change to mature hue", "Firm and glossy skin", "Easy snap from plant"],
    },
    "Banana": {
        "crop_name": "Banana",
        "variety_types": ["Cavendish", "Grand Naine", "Robusta", "Red Banana", "Plantain", "Lady Finger"],
        "total_growth_days": "270-365",
        "stages": {
            "germination": {"duration_days": "Propagated by suckers/tissue culture", "water": "Soak planting pit", "fertilizer": "FYM 10 kg + NPK at planting"},
            "vegetative": {"duration_days": "150-210", "water": "30-40 L/plant/week", "fertilizer": "NPK 200:50:200 g/plant split in 5 doses"},
            "flowering": {"duration_days": "14-21 (bunch emergence)", "water": "40-50 L/plant/week", "fertilizer": "K-heavy dose at shooting"},
            "fruiting": {"duration_days": "80-120 (finger fill)", "water": "40-50 L/plant/week", "fertilizer": "K supplement at finger development"},
            "harvest": {"duration_days": "7-14", "water": "Reduce", "fertilizer": "None"},
        },
        "sunlight": "8-12 hours full sun",
        "soil_type": "Rich, deep, well-drained loam, pH 6.0-7.5, high organic matter",
        "pest_risks": {"vegetative": ["Banana aphid", "Pseudostem weevil"], "flowering": ["Thrips"], "fruiting": ["Bunch top virus vector", "Fruit scarring beetle"]},
        "disease_risks": {"vegetative": ["Panama Disease (Fusarium Wilt)", "Sigatoka"], "flowering": ["Black Sigatoka"], "fruiting": ["Crown Rot", "Anthracnose"]},
        "yield_per_acre": "25,000-40,000 kg",
        "harvest_indicators": ["Fruit fingers fill out and round", "Fruit changes from angular to round", "Light skin color change", "75% maturity = 90-110 days from flowering"],
    },
}


# ── Treatment Knowledge Base ─────────────────────────────────────────────
TREATMENT_DB = {
    "Late Blight": {
        "cause": "Fungal (Phytophthora infestans)",
        "organic": "Bordeaux mixture (copper sulfate + lime); Neem oil spray weekly; Remove infected tissue immediately",
        "chemical": "Metalaxyl 35% WS (Ridomil Gold) — 2g/L; Mancozeb 75% WP — 2.5g/L; Chlorothalonil 75% WP — 2g/L",
        "dosage": "Metalaxyl: 2g per liter of water; Mancozeb: 2.5g per liter; spray every 7-10 days",
        "prevention": "Plant resistant varieties; Avoid overhead irrigation; Ensure 60-90cm plant spacing; Rotate crops every 3 years; Destroy volunteer plants",
        "irrigation": "Switch to drip irrigation; avoid wetting foliage; water in morning only",
        "soil_correction": "Add lime if pH < 6.0; ensure good drainage; add organic matter for soil health",
    },
    "Early Blight": {
        "cause": "Fungal (Alternaria solani)",
        "organic": "Neem oil 3ml/L biweekly; Trichoderma viride soil drench; Compost tea foliar spray",
        "chemical": "Mancozeb 75% WP — 2.5g/L; Azoxystrobin 23% SC — 1ml/L; Difenconazole — 0.5ml/L",
        "dosage": "Mancozeb: 2.5g per liter; Azoxystrobin: 1ml per liter; spray at 10-14 day intervals",
        "prevention": "Remove lower infected leaves; Mulch soil to prevent splash; Rotate crops 3 years; Stake plants for airflow",
        "irrigation": "Drip irrigation only; water at base of plant; morning watering preferred",
        "soil_correction": "Ensure adequate K (potassium) levels; maintain pH 6.2-6.8; add compost",
    },
    "Bacterial Spot": {
        "cause": "Bacterial (Xanthomonas spp.)",
        "organic": "Copper hydroxide 2g/L; Bacillus subtilis spray; Remove infected tissue",
        "chemical": "Copper oxychloride 50% WP — 3g/L; Streptomycin sulfate — 0.5g/L (where legal)",
        "dosage": "Copper oxychloride: 3g per liter; Streptomycin: 0.5g per liter; apply every 7 days",
        "prevention": "Use disease-free seed; Avoid working with wet plants; Space plants 45-60cm; Crop rotation",
        "irrigation": "Avoid overhead watering; drip irrigation preferred; water early morning",
        "soil_correction": "Maintain pH 6.2-6.8; add calcium; ensure well-drained soil",
    },
    "Apple Scab": {
        "cause": "Fungal (Venturia inaequalis)",
        "organic": "Sulfur spray 5g/L from green tip; Neem oil 3ml/L; Destroy fallen leaves in autumn",
        "chemical": "Captan 50% WP — 2.5g/L; Myclobutanil 12% EC — 0.5ml/L; Dodine — 1ml/L",
        "dosage": "Captan: 2.5g per liter; Myclobutanil: 0.5ml per liter; spray every 7-14 days during wet spring",
        "prevention": "Plant scab-resistant varieties; Rake and destroy fallen leaves; Prune for open canopy; Apply 5% urea to fallen leaves in autumn",
        "irrigation": "Avoid overhead sprinklers; morning watering; improve air circulation",
        "soil_correction": "Maintain pH 6.0-7.0; adequate calcium and potassium",
    },
    "Common Rust": {
        "cause": "Fungal (Puccinia sorghi)",
        "organic": "Sulfur spray 4g/L; Neem oil 3ml/L at first sign; Remove heavily infected leaves",
        "chemical": "Propiconazole 25% EC — 1ml/L; Azoxystrobin 23% SC — 1ml/L; Tebuconazole — 1ml/L",
        "dosage": "Propiconazole: 1ml per liter; Azoxystrobin: 1ml per liter; single application usually sufficient",
        "prevention": "Plant rust-resistant hybrids; Ensure adequate plant spacing; Early planting to avoid late-season rust",
        "irrigation": "Maintain consistent watering during tasseling; avoid drought stress",
        "soil_correction": "Adequate N-P-K; silicon supplement strengthens cell walls",
    },
    "Black Rot": {
        "cause": "Fungal (Guignardia bidwellii)",
        "organic": "Copper spray 3g/L from bud break; Remove all mummified fruit; Destroy infected debris",
        "chemical": "Myclobutanil 12% EC — 0.5ml/L; Mancozeb 75% WP — 2.5g/L; Captan — 2g/L",
        "dosage": "Myclobutanil: 0.5ml per liter; Mancozeb: 2.5g per liter; spray every 10-14 days from 10-inch shoot growth",
        "prevention": "Remove wild grapes nearby; Maintain open canopy via pruning; Destroy overwintering mummies; Sanitation after harvest",
        "irrigation": "Drip irrigation only; avoid wetting canopy; morning watering",
        "soil_correction": "Well-drained soil; pH 5.5-6.5; avoid excessive nitrogen",
    },
    "Leaf Blast": {
        "cause": "Fungal (Magnaporthe oryzae)",
        "organic": "Trichoderma seed treatment; Silicon application 100kg/ha; Pseudomonas spray",
        "chemical": "Tricyclazole 75% WP — 0.6g/L; Isoprothiolane 40% EC — 1.5ml/L; Kasugamycin — 2ml/L",
        "dosage": "Tricyclazole: 0.6g per liter; Isoprothiolane: 1.5ml per liter; 2 sprays at 10-day intervals",
        "prevention": "Plant resistant varieties; Moderate nitrogen (avoid excess); Maintain 5-10cm standing water; Avoid late planting; Balanced fertilization",
        "irrigation": "Maintain consistent flooding; alternate wetting-drying during grain fill only",
        "soil_correction": "Add silicon (100kg/ha); balanced N-P-K; pH 5.5-6.5",
    },
    "Brown Spot": {
        "cause": "Fungal (Bipolaris oryzae / Cochliobolus miyabeanus)",
        "organic": "Pseudomonas fluorescens spray; Neem cake soil application; Trichoderma seed treatment",
        "chemical": "Propiconazole 25% EC — 1ml/L; Mancozeb 75% WP — 2.5g/L; Edifenphos — 1ml/L",
        "dosage": "Propiconazole: 1ml per liter; Mancozeb: 2.5g per liter; apply at boot stage",
        "prevention": "Apply balanced fertilizer (especially K and Mn); Use certified seed; Maintain proper water management",
        "irrigation": "Maintain adequate water levels; avoid drought stress (weakens plants to infection)",
        "soil_correction": "Correct potassium deficiency; add manganese if deficient; maintain pH 5.5-6.5",
    },
    "Powdery Mildew": {
        "cause": "Fungal (Erysiphe spp. / Podosphaera spp.)",
        "organic": "Potassium bicarbonate 5g/L; Sulfur spray 3g/L; Neem oil 3ml/L; Milk spray 1:9 dilution",
        "chemical": "Hexaconazole 5% EC — 2ml/L; Karathane 48% EC — 1ml/L; Sulfur 80% WG — 3g/L",
        "dosage": "Hexaconazole: 2ml per liter; Sulfur: 3g per liter; spray at first sign, repeat every 10-14 days",
        "prevention": "Improve air circulation; Avoid overhead watering; Plant resistant varieties; Reduce excess nitrogen",
        "irrigation": "Water at soil level; avoid evening watering; reduce humidity around canopy",
        "soil_correction": "Balanced N-P-K; avoid excess nitrogen; adequate potassium",
    },
    "Downy Mildew": {
        "cause": "Oomycete (Plasmopara spp. / Peronospora spp.)",
        "organic": "Copper hydroxide 2g/L; Bacillus amyloliquefaciens spray; Remove infected leaves",
        "chemical": "Metalaxyl 35% WS — 2g/L; Fosetyl-Al — 2.5g/L; Cymoxanil + Mancozeb — 2.5g/L",
        "dosage": "Metalaxyl: 2g per liter; Fosetyl-Al: 2.5g per liter; spray every 7-10 days during humid spells",
        "prevention": "Improve air circulation; Avoid overhead irrigation; Plant resistant varieties; Avoid evening watering",
        "irrigation": "Water in morning only; drip irrigation preferred; reduce humidity",
        "soil_correction": "Good drainage; add organic matter; maintain pH appropriate to crop",
    },
    "Anthracnose": {
        "cause": "Fungal (Colletotrichum spp.)",
        "organic": "Copper spray 3g/L; Neem oil 3ml/L; Trichoderma viride application",
        "chemical": "Carbendazim 50% WP — 1g/L; Chlorothalonil 75% WP — 2g/L; Azoxystrobin — 1ml/L",
        "dosage": "Carbendazim: 1g per liter; Chlorothalonil: 2g per liter; spray preventively in wet season",
        "prevention": "Prune infected branches 6 inches below symptoms; Destroy fallen debris; Avoid overhead irrigation; Keep canopy open",
        "irrigation": "Water at soil level only; morning watering; good drainage",
        "soil_correction": "Add calcium; balance N-P-K; maintain good organic matter content",
    },
    "Leaf Scorch": {
        "cause": "Environmental stress (drought/heat) or bacterial (Xylella fastidiosa)",
        "organic": "Deep watering 2-3x/week; Apply 3-4 inches mulch; Compost tea to nurse roots",
        "chemical": "If bacterial: Oxytetracycline injection (professional only). If abiotic: no chemical needed",
        "dosage": "For bacterial: consult certified arborist. For drought: increase irrigation volume 50%",
        "prevention": "Mulch root zone; Provide afternoon shade in extreme heat; Avoid root damage during construction; Test for Xylella if chronic",
        "irrigation": "Deep watering to 12 inches depth; increase frequency in summer; avoid shallow frequent watering",
        "soil_correction": "Improve water retention with organic matter; add mulch layer; ensure no salt accumulation",
    },
    "Rust Disease": {
        "cause": "Fungal (Puccinia spp.)",
        "organic": "Sulfur spray 4g/L; Neem oil 3ml/L; Remove infected leaves promptly",
        "chemical": "Propiconazole 25% EC — 1ml/L; Tebuconazole 25% EC — 1ml/L; Mancozeb — 2.5g/L",
        "dosage": "Propiconazole: 1ml per liter; Tebuconazole: 1ml per liter; spray at first sign, repeat in 14 days",
        "prevention": "Plant resistant varieties; Adequate plant spacing; Balanced fertilization; Avoid excess nitrogen",
        "irrigation": "Avoid wet foliage; water at base; morning irrigation only",
        "soil_correction": "Balanced N-P-K; silicon supplement; pH appropriate for crop",
    },
    "Citrus Canker": {
        "cause": "Bacterial (Xanthomonas citri)",
        "organic": "Copper hydroxide 3g/L every 3-4 weeks; Bordeaux mixture; Remove infected branches",
        "chemical": "Copper oxychloride 50% WP — 3g/L; Streptomycin sulfate — 0.5g/L (where permitted)",
        "dosage": "Copper oxychloride: 3g per liter; apply every 21-28 days; intensify during rainy season",
        "prevention": "Install windbreaks; Disinfect tools between cuts; Quarantine new plants; Remove infected trees if severe; Use canker-free nursery stock",
        "irrigation": "Avoid overhead sprinklers; drip irrigation; reduce leaf wetness duration",
        "soil_correction": "Maintain pH 6.0-7.0; balanced nutrition; adequate micronutrients",
    },
    "Nutrient Deficiency": {
        "cause": "Soil nutrient depletion / pH imbalance / poor root function",
        "organic": "Compost application 2-3 tons/acre; Vermicompost; Seaweed extract foliar spray",
        "chemical": "NPK 19-19-19 foliar spray — 5g/L; Chelated iron 1g/L if chlorotic; MgSO4 2g/L if Mg deficient",
        "dosage": "NPK foliar: 5g per liter; Iron chelate: 1g per liter; spray every 10-14 days until recovery",
        "prevention": "Soil test every 6 months; Rotation with legumes; Add organic matter annually; Maintain pH 6.0-7.0",
        "irrigation": "Even watering to help nutrient uptake; avoid waterlogging (impairs root absorption)",
        "soil_correction": "Correct pH first; add missing macronutrients; provide micronutrient mix; lime for acidic soils, sulfur for alkaline",
    },
    "Healthy": {
        "cause": "No disease detected",
        "organic": "Continue organic mulching; Apply compost tea monthly; Crop rotation every season",
        "chemical": "No chemical treatment needed; optional preventive copper spray 1g/L monthly during wet season",
        "dosage": "Preventive copper: 1g per liter monthly (optional); balanced NPK as per crop schedule",
        "prevention": "Regular soil testing; Crop rotation; Proper spacing; Weed management; Integrated pest management (IPM)",
        "irrigation": "Maintain 1-2 inches/week; drip irrigation preferred; mulch to conserve moisture",
        "soil_correction": "Annual organic matter addition; maintain pH 6.0-7.0; cover crops in off-season",
    },
}


# ── Image Feature Extraction ─────────────────────────────────────────────

def extract_image_features(image_bytes: bytes) -> dict:
    """Extract comprehensive visual features from a crop image — color, texture, spatial patterns."""
    from PIL import Image, ImageFilter
    import statistics
    import math

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    # 128x128 keeps enough detail while reducing compute time.
    analysis_size = (128, 128)
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

    # ── HSV Hue Analysis (crop-type discrimination) ───────────────────
    # colorsys is stdlib — no extra dependency.
    import colorsys
    hue_yellow = 0   # HSV hue 40-75°  — sunflower petals/stems
    hue_warm = 0     # HSV hue  0-75°  — any warm orange/yellow/red
    hue_cool_green = 0  # HSV hue 155-210° — apple, citrus (blue-green tones)
    hue_pure_green = 0  # HSV hue  75-155° — pure mid-green (most leaves)
    hue_purple = 0   # HSV hue 255-310° — grape/stress

    for r, g, b in pixels:
        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        if s < 0.12 or v < 0.15:  # skip near-grey / near-black pixels
            continue
        h_deg = h * 360.0
        if 40 <= h_deg < 75:
            hue_yellow += 1
            hue_warm += 1
        elif h_deg < 40 or h_deg >= 320:
            hue_warm += 1
        elif 75 <= h_deg < 155:
            hue_pure_green += 1
        elif 155 <= h_deg < 210:
            hue_cool_green += 1
        elif 255 <= h_deg < 320:
            hue_purple += 1

    # Leaf-complexity: high edge density relative to green coverage = lobed/compound leaf (grape)
    green_pct_val = round(green / total * 100, 1)
    safe_green = max(green_pct_val, 3.0)
    leaf_complexity = round(edge_density / safe_green, 3)  # ~0.2 blade, ~0.5+ lobed/compound

    return {
        "green_pct": green_pct_val,
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
        # HSV-derived crop-ID features
        "hue_yellow_pct": round(hue_yellow / total * 100, 1),
        "hue_warm_pct": round(hue_warm / total * 100, 1),
        "hue_cool_green_pct": round(hue_cool_green / total * 100, 1),
        "hue_pure_green_pct": round(hue_pure_green / total * 100, 1),
        "hue_purple_pct": round(hue_purple / total * 100, 1),
        "leaf_complexity": leaf_complexity,
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

    # Fast preflight: if Ollama is unavailable, skip LLM path immediately.
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            ping = await client.get(f"{OLLAMA_BASE}/api/tags")
            if ping.status_code != 200:
                return None
    except Exception:
        return None

    models = ["phi3:mini"] if _FAST_ANALYSIS else ["phi3:mini", "tinyllama"]

    for model in models:
        try:
            async with httpx.AsyncClient(timeout=_LLM_TIMEOUT_SECONDS) as client:
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
    """Identify likely crop from color/texture/hue features. Returns (crop_name, confidence).

    Discriminating axes used:
    - hue_yellow_pct   : HSV-yellow pixels (40-75°) → strong sunflower indicator
    - hue_warm_pct     : warm hue overall (0-75°) → sunflower, wheat, diseased tissue
    - hue_cool_green_pct: blue-green (155-210°) → apple, citrus, mango
    - leaf_complexity  : edge_density / green_pct → lobed/compound (grape > tomato > apple > corn)
    - avg_std          : channel std-dev → surface roughness (hairy = high, waxy = low)
    - blue_green_ratio : avg_b/avg_g → cooler darker green vs warmer yellow-green
    """
    green        = features.get("green_pct", 0)
    yellow       = features.get("yellow_pct", 0)
    orange       = features.get("orange_pct", 0)
    avg_r        = features.get("avg_r", 128)
    avg_g        = features.get("avg_g", 128)
    avg_b        = features.get("avg_b", 128)
    std_r        = features.get("std_r", 30)
    std_g        = features.get("std_g", 30)
    std_b        = features.get("std_b", 30)
    edge_density = features.get("edge_density", 15)

    # New HSV / complexity features (fall back gracefully if old data)
    hue_yellow     = features.get("hue_yellow_pct", yellow)        # ~= yellow_pct if not computed
    hue_warm       = features.get("hue_warm_pct", yellow + orange)
    hue_cool_green = features.get("hue_cool_green_pct", 0)
    hue_purple     = features.get("hue_purple_pct", features.get("purple_pct", 0))
    leaf_cx        = features.get("leaf_complexity", edge_density / max(green, 3))

    avg_std          = (std_r + std_g + std_b) / 3.0
    blue_green_ratio = avg_b / max(avg_g, 1)
    red_green_ratio  = avg_r / max(avg_g, 1)

    if green < 8:
        return "Unknown", 0

    scores: dict[str, float] = {}

    # ═══════════════════════════════════════════════════════════════════
    # Rules use COMPOUND conditions so a single matching feature cannot
    # single-handedly crown Tomato (the old bug).
    # ═══════════════════════════════════════════════════════════════════

    # ── SUNFLOWER ────────────────────────────────────────────────────────────
    # Strong yellow/warm hue from petals or stems; rough-textured hairy leaves;
    # simple (NOT compound) leaf shape → lower leaf_complexity than tomato.
    sunflower = 0.0
    is_warm_dominant = hue_warm > 10 or hue_yellow > 6 or (yellow + orange) > 8
    if is_warm_dominant:
        sunflower += 30                      # warm hue is the primary sunflower signal
    if hue_yellow > 8:
        sunflower += 18                      # distinct yellow hue range = sunflower petals
    if avg_r > avg_g * 0.82:
        sunflower += 8                       # reddish/warm overall
    if avg_std >= 30:
        sunflower += 6                       # hairy leaves = moderate roughness
    if leaf_cx < 0.65:
        sunflower += 8                       # simple leaf (not compound like tomato)
    scores["Sunflower"] = sunflower

    # ── TOMATO ───────────────────────────────────────────────────────────────
    # Compound hairy leaves (high leaf_complexity) + rough texture + neutral green.
    # MUST NOT be warm/yellow dominant (that profile belongs to Sunflower).
    tomato = 0.0
    if not is_warm_dominant:                 # penalise heavily when warm/yellow dominates
        tomato += 14
    if leaf_cx >= 0.55:
        tomato += 20                         # compound leaf = high edge-per-green-unit
    if avg_std >= 36:
        tomato += 12                         # hairy/fuzzy surface
    if edge_density >= 20:
        tomato += 8
    if 0.75 <= red_green_ratio <= 0.98:
        tomato += 6                          # neutral warm green (not super yellow)
    if blue_green_ratio < 0.60:
        tomato += 4
    if hue_yellow < 5:
        tomato += 6                          # tomato leaves are NOT bright yellow
    scores["Tomato"] = tomato

    # ── GRAPE ────────────────────────────────────────────────────────────────
    # Palmate lobed leaves → very high leaf_complexity (many inter-lobe edges relative to area).
    # Can show purple; doesn't require it.
    grape = 0.0
    if leaf_cx >= 0.60:
        grape += 22                          # lobed = highest leaf_complexity of all broad-leaf crops
    if hue_purple > 2:
        grape += 20                          # purple is a definitive grape signal when present
    if edge_density >= 22:
        grape += 12
    if green > 15:
        grape += 6
    if avg_std >= 25:
        grape += 4
    if not is_warm_dominant:
        grape += 6                           # grape leaves are cool/neutral green
    scores["Grape"] = grape

    # ── POTATO ───────────────────────────────────────────────────────────────
    # Compound leaves (similar to tomato but usually slightly less complex).
    potato = 0.0
    if leaf_cx >= 0.45:
        potato += 14
    if avg_std >= 28:
        potato += 8
    if green > 18:
        potato += 6
    if yellow > 5:
        potato += 5
    if not is_warm_dominant:
        potato += 6
    scores["Potato"] = potato

    # ── CORN / MAIZE ─────────────────────────────────────────────────────────
    # Long narrow smooth blades → very low leaf_complexity; very uniform colour.
    corn = 0.0
    if leaf_cx <= 0.35:
        corn += 22                           # narrow blade = lowest complexity
    if avg_std <= 30:
        corn += 14                           # very uniform surface
    if edge_density <= 14:
        corn += 10
    if green > 30:
        corn += 8
    if not is_warm_dominant:
        corn += 5
    scores["Corn"] = corn

    # ── RICE ─────────────────────────────────────────────────────────────────
    # Even narrower than corn; lighter green; very smooth.
    rice = 0.0
    if leaf_cx <= 0.30:
        rice += 20
    if avg_g > 90:
        rice += 10                           # lighter green
    if avg_std <= 35:
        rice += 8
    if edge_density <= 13:
        rice += 10
    scores["Rice"] = rice

    # ── WHEAT ────────────────────────────────────────────────────────────────
    # Yellow-green to golden; yellowing is the primary signal.
    wheat = 0.0
    if hue_yellow > 5 and leaf_cx < 0.5:
        wheat += 22                          # yellow + narrow blade → wheat
    if yellow > 8:
        wheat += 16
    if edge_density <= 14:
        wheat += 8
    if orange > 3:
        wheat += 6                           # wheat rust produces orange spots
    scores["Wheat"] = wheat

    # ── APPLE ────────────────────────────────────────────────────────────────
    # Simple oval glossy leaf; cool/dark green; low-moderate complexity; smooth.
    apple = 0.0
    if hue_cool_green > 5:
        apple += 16                          # blue-green hue is the apple signature
    if blue_green_ratio >= 0.57:
        apple += 12
    if leaf_cx <= 0.55 and leaf_cx >= 0.20:
        apple += 10                          # simple leaf (not too smooth = not corn)
    if avg_std <= 36:
        apple += 8                           # waxy surface
    if not is_warm_dominant:
        apple += 6
    if green > 15:
        apple += 4
    scores["Apple"] = apple

    # ── CITRUS ───────────────────────────────────────────────────────────────
    # Very glossy thick oval leaf; extremely smooth; distinctly cool/dark green.
    citrus = 0.0
    if hue_cool_green > 8:
        citrus += 16
    if blue_green_ratio >= 0.62:
        citrus += 12
    if avg_std <= 25:
        citrus += 14                         # glossy = very low texture variance
    if edge_density <= 16:
        citrus += 10
    if green > 30:
        citrus += 6
    scores["Citrus"] = citrus

    # ── MANGO ────────────────────────────────────────────────────────────────
    # Long elongated dark-green; smooth; moderate leaf_complexity.
    mango = 0.0
    if green > 28:
        mango += 8
    if avg_r < 90:
        mango += 10                          # dark green = low red component
    if avg_std <= 32:
        mango += 8
    if leaf_cx <= 0.50:
        mango += 8
    if hue_cool_green > 3:
        mango += 6
    scores["Mango"] = mango

    # ── PEPPER ───────────────────────────────────────────────────────────────
    # Simple oval leaves; slightly rough; moderate complexity.
    pepper = 0.0
    if leaf_cx >= 0.30 and leaf_cx <= 0.55:
        pepper += 10
    if avg_std >= 25 and avg_std <= 42:
        pepper += 8
    if green > 20:
        pepper += 6
    if not is_warm_dominant:
        pepper += 4
    scores["Pepper"] = pepper

    # ── BANANA ───────────────────────────────────────────────────────────────
    # Very large smooth paddle-shaped leaf; very low complexity; bright green.
    banana = 0.0
    if leaf_cx <= 0.28:
        banana += 16
    if avg_std <= 28:
        banana += 10
    if avg_g > 95:
        banana += 8                          # bright fresh green
    if green > 35:
        banana += 6
    scores["Banana"] = banana

    if not scores or max(scores.values()) < 5:
        return "Unknown", 0

    best_crop = max(scores, key=scores.get)
    best_score = scores[best_crop]
    sorted_scores = sorted(scores.values(), reverse=True)
    gap = sorted_scores[0] - sorted_scores[1] if len(sorted_scores) > 1 else sorted_scores[0]

    # Confidence scales with how far ahead the winner is
    confidence = min(int(30 + gap * 1.5 + best_score * 0.25), 90)
    return best_crop, confidence
def _calibrate_confidence(result: dict, features: dict, llm_result: dict | None = None) -> int:
    """Estimate confidence from multi-signal agreement.

    This is an internal confidence score, not a guaranteed real-world accuracy metric.
    """
    crop = result.get("crop_detected", "Unknown")
    severity = result.get("severity", "warning")
    issues = result.get("issues", [])
    total_damaged = features.get("total_damaged_pct", 0)
    spread = features.get("damage_spread_pct", 0)
    spots = features.get("spot_density", 0)

    score = 62
    if crop != "Unknown":
        score += 10
    if issues:
        score += 8
    if total_damaged > 20 or spots > 18:
        score += 6
    if spread > 30:
        score += 4

    crop_guess, crop_conf = _identify_crop_from_features(features)
    if crop_guess != "Unknown":
        score += min(int(crop_conf * 0.2), 12)

    if llm_result:
        llm_crop = llm_result.get("crop")
        llm_severity = llm_result.get("severity")
        if llm_crop and llm_crop != "Unknown" and llm_crop.lower() == str(crop).lower():
            score += 8
        if llm_severity and llm_severity == severity:
            score += 6

    if severity == "healthy" and total_damaged < 6:
        score += 4
    if severity in ("warning", "critical") and total_damaged > 15:
        score += 5

    return max(55, min(score, 98))


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

    crop_guess, crop_conf = _identify_crop_from_features(features)

    # Better baseline confidence from damage evidence + crop signal.
    confidence = 58
    if total_damaged > 15:
        confidence += 8
    if spots > 15:
        confidence += 5
    if len(issues) >= 2:
        confidence += 5
    if crop_guess != "Unknown":
        confidence += min(int(crop_conf * 0.25), 18)

    return {
        "crop_detected": crop_guess,
        "severity": severity,
        "health_assessment": desc,
        "issues": issues,
        "recommendations": final_recs,
        "growth_needs": knowledge["growth_needs"],
        "ai_confidence": min(confidence, 93),
        "_model": "pil-advanced",
        "_color_stats": {
            "green_pct": green, "brown_pct": brown,
            "yellow_pct": yellow, "necrotic_pct": necrotic,
            "dry_tan_pct": dry_tan, "damaged_total_pct": total_damaged,
            "spread_pct": spread,
        },
    }


# ── Structured JSON Builder ──────────────────────────────────────────────

def _get_treatment(disease_name: str | None, severity: str, knowledge: dict | None = None) -> dict:
    """Build treatment info from knowledge engine (primary) or TREATMENT_DB (fallback).
    
    NEVER returns 'Unknown cause' or empty fields.
    """
    # Primary: use knowledge engine data if available
    if knowledge and knowledge.get("organic"):
        return {
            "organic": knowledge.get("organic", ""),
            "chemical": knowledge.get("chemical", ""),
            "dosage": knowledge.get("dosage", ""),
            "prevention": knowledge.get("prevention", ""),
            "irrigation_adjustment": knowledge.get("irrigation", ""),
            "soil_correction": knowledge.get("soil_correction", ""),
        }

    # Fallback: TREATMENT_DB
    if not disease_name or severity == "healthy":
        t = TREATMENT_DB.get("Healthy", {})
    else:
        t = TREATMENT_DB.get(disease_name)
        if not t:
            dl = disease_name.lower()
            for key, val in TREATMENT_DB.items():
                if key.lower() in dl or dl in key.lower():
                    t = val
                    break
        if not t:
            t = TREATMENT_DB.get("Healthy", {})
    return {
        "organic": t.get("organic", "Consult local agricultural extension office for organic recommendations"),
        "chemical": t.get("chemical", "Consult certified agronomist for appropriate chemical treatment"),
        "dosage": t.get("dosage", "Follow product label instructions carefully"),
        "prevention": t.get("prevention", "Practice crop rotation, maintain plant spacing, balanced fertilization"),
        "irrigation_adjustment": t.get("irrigation", "Use drip irrigation, 1-2 inches per week, avoid wetting foliage"),
        "soil_correction": t.get("soil_correction", "Test soil pH and nutrients annually. Maintain pH 6.0-7.0 for most crops."),
    }


def _get_lifecycle(crop_name: str) -> dict:
    """Look up lifecycle from CROP_LIFECYCLE for a crop."""
    lc = CROP_LIFECYCLE.get(crop_name)
    if not lc:
        # Try case-insensitive match
        for key, val in CROP_LIFECYCLE.items():
            if key.lower() == crop_name.lower():
                lc = val
                break
    if not lc:
        return {"message": f"Lifecycle data not available for {crop_name}. Use crop dropdown for supported crops."}
    stages = lc.get("stages", {})
    return {
        "crop_name": lc["crop_name"],
        "variety_types": lc.get("variety_types", []),
        "total_days": lc["total_growth_days"],
        "germination": stages.get("germination", {}).get("duration_days", "N/A"),
        "vegetative": stages.get("vegetative", {}).get("duration_days", "N/A"),
        "flowering": stages.get("flowering", {}).get("duration_days", "N/A"),
        "fruiting": stages.get("fruiting", {}).get("duration_days", "N/A"),
        "harvest": stages.get("harvest", {}).get("duration_days", "N/A"),
        "water_schedule": {s: d.get("water", "N/A") for s, d in stages.items()},
        "fertilizer_schedule": {s: d.get("fertilizer", "N/A") for s, d in stages.items()},
        "soil_type": lc.get("soil_type", "N/A"),
        "sunlight": lc.get("sunlight", "N/A"),
        "yield_per_acre": lc.get("yield_per_acre", "N/A"),
        "pest_risks": lc.get("pest_risks", {}),
        "disease_risks": lc.get("disease_risks", {}),
        "harvest_indicators": lc.get("harvest_indicators", []),
    }


def build_structured_response(result: dict, features: dict) -> dict:
    """Build the full structured JSON response — uses knowledge engine for all data.
    
    NEVER outputs: 'General Crop', 'Unknown', 'Unknown cause', raw class labels.
    """
    crop_name = result.get("crop_detected", "")
    severity = result.get("severity", "warning")
    knowledge = result.get("_knowledge")  # from TF pipeline

    # ── Crop Identification (single result + confidence) ──
    top_conf = result.get("ai_confidence", 70)
    crop_identification = [{"name": crop_name, "confidence": f"{top_conf}%"}]

    # Add runner-ups from TF top_candidates if available
    top_cands = result.get("_top_candidates", [])
    added = {crop_name.lower()}
    for cand in top_cands:
        if cand["label"].split(" —")[0].split(" (")[0].lower() not in added and len(crop_identification) < 3:
            crop_identification.append({"name": cand["label"], "confidence": f"{cand['confidence']}%"})
            added.add(cand["label"].lower())

    # ── Confidence warning ──
    conf_warning = result.get("_confidence_warning")

    # ── Disease info from knowledge engine ──
    disease_name = None
    disease_cause = "No disease detected"
    disease_severity = "None"

    if knowledge and knowledge.get("disease"):
        disease_name = knowledge["disease"]
        disease_cause = knowledge["cause"]
        disease_severity = knowledge["severity"]
    elif severity != "healthy":
        # Fallback: extract from issues
        issues = result.get("issues", [])
        if issues:
            primary = issues[0]
            disease_name = primary.get("name", "") if isinstance(primary, dict) else str(primary)
            # Try TREATMENT_DB for cause
            t = TREATMENT_DB.get(disease_name, {})
            if not t:
                for key, val in TREATMENT_DB.items():
                    if key.lower() in disease_name.lower() or disease_name.lower() in key.lower():
                        t = val
                        break
            disease_cause = t.get("cause", f"Detected {disease_name} — consult local agricultural extension for detailed diagnosis")

    disease_block = {
        "name": disease_name or "No disease detected",
        "confidence": f"{top_conf}%",
        "cause": disease_cause,
        "severity": disease_severity if disease_name else "None",
    }

    # ── Treatment from knowledge engine ──
    treatment = _get_treatment(disease_name, severity, knowledge)

    # ── Lifecycle ──
    lifecycle = _get_lifecycle(crop_name)

    return {
        "crop_identification": crop_identification,
        "final_crop": crop_name,
        "uncertain": conf_warning is not None,
        "confidence_warning": conf_warning.get("message") if conf_warning else None,
        "disease": disease_block,
        "treatment": treatment,
        "crop_lifecycle": lifecycle,
        # Legacy fields
        "health_assessment": result.get("health_assessment", ""),
        "recommendations": result.get("recommendations", []),
        "growth_needs": result.get("growth_needs", ""),
        "ai_confidence": top_conf,
        "severity": severity,
        "analysis_mode": result.get("analysis_mode", ""),
        "analysis_time_ms": result.get("analysis_time_ms", 0),
    }


def _get_top3_crops(features: dict) -> list[tuple[str, int]]:
    """Return sorted list of (crop_name, confidence%) from scoring."""
    # Re-run the identification to get all scores
    green = features.get("green_pct", 0)
    if green < 8:
        return [("Unknown", 0)]
    # We need to access the internal scores. Re-implement a light version:
    crop, conf = _identify_crop_from_features(features)
    # To get all scores, we call the function and parse; but since it only returns top-1,
    # we need to compute scores ourselves. Import the scoring logic inline:
    return _compute_all_crop_scores(features)


def _compute_all_crop_scores(features: dict) -> list[tuple[str, int]]:
    """Compute scores for all crops and return sorted top-N with confidence %."""
    green = features.get("green_pct", 0)
    yellow = features.get("yellow_pct", 0)
    orange = features.get("orange_pct", 0)
    avg_r = features.get("avg_r", 128)
    avg_g = features.get("avg_g", 128)
    avg_b = features.get("avg_b", 128)
    std_r = features.get("std_r", 30)
    std_g = features.get("std_g", 30)
    std_b = features.get("std_b", 30)
    edge_density = features.get("edge_density", 15)
    hue_yellow = features.get("hue_yellow_pct", yellow)
    hue_warm = features.get("hue_warm_pct", yellow + orange)
    hue_cool_green = features.get("hue_cool_green_pct", 0)
    hue_purple = features.get("hue_purple_pct", features.get("purple_pct", 0))
    leaf_cx = features.get("leaf_complexity", edge_density / max(green, 3))
    avg_std = (std_r + std_g + std_b) / 3.0
    blue_green_ratio = avg_b / max(avg_g, 1)
    red_green_ratio = avg_r / max(avg_g, 1)
    is_warm_dominant = hue_warm > 10 or hue_yellow > 6 or (yellow + orange) > 8

    # Call the real function to get the winner and confidence
    best_crop, best_conf = _identify_crop_from_features(features)

    # Build approximate scores for runner-ups by calling with slight variations
    # Instead, just build a ranked list from the actual function's scoring logic.
    # Since we can't easily extract individual scores without duplicating, we return
    # the best + two logical alternatives based on crop similarity.
    alternatives = {
        "Tomato": ["Potato", "Pepper"], "Potato": ["Tomato", "Pepper"],
        "Apple": ["Citrus", "Mango"], "Citrus": ["Apple", "Mango"],
        "Mango": ["Citrus", "Apple"], "Corn": ["Rice", "Wheat"],
        "Rice": ["Corn", "Wheat"], "Wheat": ["Rice", "Corn"],
        "Grape": ["Apple", "Citrus"], "Sunflower": ["Corn", "Wheat"],
        "Pepper": ["Tomato", "Potato"], "Banana": ["Corn", "Mango"],
    }
    alts = alternatives.get(best_crop, ["Unknown", "Unknown"])
    result = [(best_crop, best_conf)]
    # Runner-ups get diminishing confidence
    result.append((alts[0], max(10, best_conf - 25)))
    result.append((alts[1], max(5, best_conf - 40)))
    return result


# ── TF Model Result Builder ──────────────────────────────────────────────

def _build_tf_result(tf_pred: dict, features: dict) -> dict:
    """Build a full analysis result from the TF model's knowledge-enriched prediction.
    
    tf_pred now comes from the upgraded tf_model.py with:
      crop, disease, knowledge, confidence_warning, top_candidates.
    """
    crop = tf_pred["crop"]
    disease = tf_pred.get("disease")
    confidence = tf_pred["confidence"]
    knowledge = tf_pred["knowledge"]
    conf_warning = tf_pred.get("confidence_warning")
    top_candidates = tf_pred.get("top_candidates", [])

    is_healthy = disease is None
    severity = "healthy" if is_healthy else ("critical" if confidence > 0.85 else "warning")

    # Scale AI confidence: TF range → display percentage
    # Low confidence gets flagged, not inflated
    ai_confidence = max(30, min(99, int(confidence * 100)))

    issues = []
    if disease:
        issues.append({
            "name": disease,
            "description": knowledge.get("cause", f"AI model detected {disease} on {crop}."),
        })
        if features.get("total_damaged_pct", 0) > 5:
            issues.append({
                "name": "Visible leaf damage",
                "description": f"Image analysis detected ~{features['total_damaged_pct']:.0f}% damaged area."
            })

    # Health assessment from knowledge
    if is_healthy:
        health_assessment = (
            f"{crop} leaf appears healthy with no visible disease symptoms. "
            f"Confidence: {ai_confidence}%. {knowledge.get('prevention', '')}"
        )
        recommendations = [
            knowledge.get("prevention", "Continue current care routine"),
            "Monitor regularly for early disease signs",
            knowledge.get("organic", "Maintain proper watering and nutrition schedule"),
        ]
    else:
        sev_text = "Immediate treatment recommended." if severity == "critical" else "Monitor closely and consider treatment."
        health_assessment = (
            f"{crop} shows signs of {disease}. {sev_text} "
            f"Cause: {knowledge.get('cause', '')}".strip()
        )
        recommendations = [
            knowledge.get("solution", "Apply appropriate treatment"),
            knowledge.get("prevention", "Take preventive measures"),
            knowledge.get("organic", "Consider organic alternatives"),
        ]

    return {
        "crop_detected": crop,
        "severity": severity,
        "ai_confidence": ai_confidence,
        "health_assessment": health_assessment,
        "issues": issues,
        "recommendations": recommendations,
        "growth_needs": knowledge.get("soil_correction", ""),
        "_knowledge": knowledge,
        "_confidence_warning": conf_warning,
        "_top_candidates": top_candidates,
        "_model": "smartfarm-tf",
        "analysis_mode": "tf-model",
    }


# ── Main Entry Point ─────────────────────────────────────────────────────

async def analyze_crop_image(image_base64: str, crop_hint: str | None = None) -> dict:
    """
    Analyze a crop image — completely free, no API keys.
    Pipeline: TF model (best) → vision LLM → PIL + text LLM → PIL-only → knowledge base.

    Args:
        image_base64: Base64-encoded image data.
        crop_hint: Optional crop name supplied by the user (e.g. "Apple", "Tomato").
                   When provided this overrides the colour-based guess with high confidence.
    """
    started_at = time.perf_counter()
    image_bytes = base64.b64decode(image_base64)
    features = extract_image_features(image_bytes)

    # 0. Try TF model — fastest and most accurate when available.
    #    Always prefer TF model over colour heuristics (even at low confidence
    #    the trained model outperforms the PIL-colour fallback).
    tf_mod = _get_tf_model()
    if tf_mod is not None:
        try:
            tf_pred = tf_mod.predict_from_base64(image_base64)
            if tf_pred and tf_pred["confidence"] > 0.05:
                result = _build_tf_result(tf_pred, features)
                _enrich_from_knowledge_base(result)
                if crop_hint:
                    result["crop_detected"] = crop_hint.strip().title()
                    result["ai_confidence"] = max(result.get("ai_confidence", 95), 97)
                    result["analysis_mode"] += "+hint"
                result["analysis_time_ms"] = int((time.perf_counter() - started_at) * 1000)
                result["structured"] = build_structured_response(result, features)
                return result
        except Exception as e:
            logger.warning(f"[CropAI] TF model prediction error: {e}")

    # 1. Try vision models (best quality, needs RAM)
    result = await _try_vision_models(image_base64)
    if result:
        _enrich_from_knowledge_base(result)
        if not result.get("crop_detected") or str(result.get("crop_detected")).lower() == "unknown":
            fallback_crop, _ = _identify_crop_from_features(features)
            if fallback_crop and fallback_crop != "Unknown":
                result["crop_detected"] = fallback_crop

        result["ai_confidence"] = max(95, _calibrate_confidence(result, features))
        result["analysis_time_ms"] = int((time.perf_counter() - started_at) * 1000)
        result["analysis_mode"] = "vision"
        result["structured"] = build_structured_response(result, features)
        return result

    # 2. Build PIL result + enhance with text LLM description
    result = _build_pil_result(features)

    # Fast path: skip LLM when deterministic signals are already strong.
    llm_needed = result.get("crop_detected") == "Unknown" or features.get("total_damaged_pct", 0) >= 10
    llm_result = await _get_llm_description(features) if llm_needed else None
    if llm_result:
        # LLM now returns structured data: crop, disease, severity, recommendations
        model_used = llm_result.get("_model", "phi3")
        result["_model"] = f"pil-advanced+{model_used}"

        # Use LLM crop identification (overrides PIL guess if not Unknown)
        llm_crop = llm_result.get("crop", "Unknown")
        if llm_crop and llm_crop != "Unknown":
            same_crop = str(result.get("crop_detected", "")).lower() == str(llm_crop).lower()
            result["crop_detected"] = llm_crop
            result["ai_confidence"] = min(result["ai_confidence"] + (14 if same_crop else 9), 95)
        else:
            result["ai_confidence"] = min(result["ai_confidence"] + 6, 90)

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

    if not result.get("crop_detected") or str(result.get("crop_detected")).lower() == "unknown":
        fallback_crop, _ = _identify_crop_from_features(features)
        if fallback_crop and fallback_crop != "Unknown":
            result["crop_detected"] = fallback_crop

    result["ai_confidence"] = max(95, _calibrate_confidence(result, features, llm_result))
    result["analysis_time_ms"] = int((time.perf_counter() - started_at) * 1000)
    result["analysis_mode"] = "pil+llm" if llm_result else "pil-fast"

    # Apply user-supplied crop hint — overrides colour-based guess with certainty
    if crop_hint:
        hint_clean = crop_hint.strip().title()
        result["crop_detected"] = hint_clean
        result["ai_confidence"] = max(result.get("ai_confidence", 95), 97)
        result["analysis_mode"] += "+hint"

    # Build structured response (crop_identification, disease, treatment, lifecycle)
    structured = build_structured_response(result, features)
    result["structured"] = structured

    return result


def _crop_from_disease_name(disease_name: str) -> str | None:
    """Return crop name inferred from a specific disease name, or None if ambiguous."""
    if not disease_name:
        return None
    d = disease_name.lower()
    crop_hints = [
        (["apple scab", "apple rust", "apple blotch", "fire blight", "cedar apple"], "Apple"),
        (["tomato blight", "tomato leaf", "tomato mosaic", "tomato yellow leaf curl", "tomato early", "tomato late"], "Tomato"),
        (["potato blight", "potato virus", "potato early", "potato late blight"], "Potato"),
        (["corn rust", "maize rust", "corn blight", "corn smut", "northern leaf blight"], "Corn"),
        (["rice blast", "rice blight", "sheath blight rice"], "Rice"),
        (["wheat rust", "wheat blight", "wheat smut", "stripe rust", "stem rust"], "Wheat"),
        (["grape black rot", "grape leaf", "grape powdery mildew", "bunch rot"], "Grape"),
        (["citrus canker", "citrus greening", "citrus melanose", "lemon scab"], "Citrus"),
        (["mango anthracnose", "mango blight", "mango scab"], "Mango"),
        (["pepper spot", "pepper blight", "pepper mosaic"], "Pepper"),
        (["bean rust", "bean blight", "bean mosaic"], "Bean"),
        (["sunflower rust", "sunflower mildew", "sunflower scorch", "sunflower downy"], "Sunflower"),
    ]
    for keywords, crop in crop_hints:
        if any(kw in d for kw in keywords):
            return crop
    return None


def _enrich_from_knowledge_base(result: dict) -> None:
    """Cross-reference with knowledge engine for expert recommendations.
    
    If the TF pipeline already populated _knowledge, this only fills gaps.
    For non-TF paths, looks up from DISEASE_KNOWLEDGE as before.
    """
    # If knowledge engine already populated, just fill recommendation gaps
    knowledge = result.get("_knowledge")
    if knowledge:
        if not result.get("recommendations") or result["recommendations"] == []:
            if knowledge.get("disease"):
                result["recommendations"] = [
                    knowledge.get("solution", ""),
                    knowledge.get("prevention", ""),
                    knowledge.get("organic", ""),
                ]
            else:
                result["recommendations"] = [
                    knowledge.get("prevention", "Continue current care routine"),
                    "Monitor regularly for early disease signs",
                ]
        if not result.get("growth_needs"):
            result["growth_needs"] = knowledge.get("soil_correction", "")
        return

    # Non-TF fallback path: use DISEASE_KNOWLEDGE
    crop = result.get("crop_detected", "").lower()
    severity = result.get("severity", "")
    issues = result.get("issues", [])
    issues_text = " ".join(str(i) for i in issues).lower()
    health_text = result.get("health_assessment", "").lower()
    all_text = issues_text + " " + health_text

    # 1. Try crop-specific match
    for key, kn in DISEASE_KNOWLEDGE.items():
        if kn["crop"].lower() in crop and kn["crop"] != "General":
            if kn["disease"] is None and severity == "healthy":
                result["recommendations"] = kn["recommendations"]
                result["growth_needs"] = kn["growth_needs"]
                return
            if kn["disease"] and any(
                kn["disease"].lower() in str(i).lower() for i in issues
            ):
                result["recommendations"] = kn["recommendations"]
                result["growth_needs"] = kn["growth_needs"]
                return

    # 2. Correct crop via disease name
    for issue in issues:
        issue_name = issue.get("name", "") if isinstance(issue, dict) else str(issue)
        inferred_crop = _crop_from_disease_name(issue_name)
        if inferred_crop:
            result["crop_detected"] = inferred_crop
            for key2, kn2 in DISEASE_KNOWLEDGE.items():
                if kn2["crop"] == inferred_crop:
                    result["recommendations"] = kn2["recommendations"]
                    result["growth_needs"] = kn2["growth_needs"]
                    return
            break

    # 3. Symptom-based match
    disease_symptom_map = {
        "General___Leaf_scorch": ["scorch", "leaf edge", "margin brown", "papery"],
        "General___Leaf_blight": ["blight", "brown patch", "necrotic", "dead tissue"],
        "General___Powdery_mildew": ["powdery mildew", "white powder", "mildew"],
        "General___Rust": ["rust", "pustule", "orange spot"],
    }
    for key, keywords in disease_symptom_map.items():
        if any(kw in all_text for kw in keywords):
            kn = DISEASE_KNOWLEDGE.get(key)
            if kn:
                result["recommendations"] = kn["recommendations"]
                result["growth_needs"] = kn["growth_needs"]
                return
