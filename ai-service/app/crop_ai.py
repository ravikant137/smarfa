# ============================================================
# SMART AGRI AI — PLANTIX LEVEL DETECTION ENGINE
# Production Grade Crop + Disease Detection
# ============================================================

import cv2
import numpy as np
import base64
import io
import math
from PIL import Image, ImageFilter
from typing import Dict, Optional


def _sanitise(obj):
    """Recursively convert numpy scalars/bools to plain Python types."""
    if isinstance(obj, dict):
        return {k: _sanitise(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitise(v) for v in obj]
    # numpy scalar types
    try:
        import numpy as _np
        if isinstance(obj, _np.integer):
            return int(obj)
        if isinstance(obj, _np.floating):
            return float(obj)
        if isinstance(obj, _np.bool_):
            return bool(obj)
    except ImportError:
        pass
    return obj


# ============================================================
# CROP LIFECYCLE DATA
# ============================================================

CROP_LIFECYCLE = {
    "Tomato": {
        "stages": ["Seedling", "Vegetative", "Flowering", "Fruiting", "Harvest"],
        "duration_days": [14, 30, 20, 40, 10],
        "water_needs": ["Low", "Medium", "High", "High", "Medium"],
        "nutrients": ["N-P-K balanced", "High N", "High P-K", "High P-K", "Low N"],
    },
    "Wheat": {
        "stages": ["Germination", "Tillering", "Stem Extension", "Heading", "Ripening", "Harvest"],
        "duration_days": [10, 25, 30, 15, 20, 5],
        "water_needs": ["Medium", "Medium", "High", "Medium", "Low", "Very Low"],
        "nutrients": ["N-P-K balanced", "High N", "High N", "High P-K", "Low", "None"],
    },
    "Rice": {
        "stages": ["Seedling", "Tillering", "Panicle Initiation", "Heading", "Grain Filling", "Harvest"],
        "duration_days": [21, 30, 30, 10, 30, 5],
        "water_needs": ["Flooded", "Flooded", "Flooded", "Flooded", "Drained", "Dry"],
        "nutrients": ["N-P-K balanced", "High N", "High P-K", "High P-K", "Low N", "None"],
    },
    "Corn": {
        "stages": ["Germination", "Vegetative", "Tasseling", "Silking", "Grain Fill", "Harvest"],
        "duration_days": [7, 40, 10, 5, 35, 7],
        "water_needs": ["Low", "Medium", "High", "Very High", "High", "Low"],
        "nutrients": ["N-P-K balanced", "High N", "High N", "High P-K", "Medium", "None"],
    },
    "Apple": {
        "stages": ["Dormancy", "Bud Break", "Flowering", "Fruit Set", "Fruit Growth", "Harvest"],
        "duration_days": [120, 20, 14, 21, 90, 30],
        "water_needs": ["None", "Low", "Medium", "Medium", "High", "Medium"],
        "nutrients": ["None", "High N", "High P-K", "High P-K", "High P-K", "Low N"],
    },
    "Potato": {
        "stages": ["Sprout Development", "Vegetative", "Tuber Initiation", "Tuber Bulking", "Maturation", "Harvest"],
        "duration_days": [14, 30, 14, 45, 20, 7],
        "water_needs": ["Low", "Medium", "High", "Very High", "Medium", "Low"],
        "nutrients": ["N-P-K balanced", "High N", "High P-K", "High P-K", "Low", "None"],
    },
    "Grape": {
        "stages": ["Dormancy", "Bud Break", "Shoot Growth", "Flowering", "Berry Growth", "Harvest"],
        "duration_days": [90, 20, 30, 14, 60, 30],
        "water_needs": ["None", "Low", "Medium", "Medium", "High", "Low"],
        "nutrients": ["None", "High N", "High N", "High P-K", "High P-K", "Low N"],
    },
}


# ============================================================
# TREATMENT DATABASE
# ============================================================

TREATMENT_DB = {
    "Late Blight": {
        "crop": ["Tomato", "Potato"],
        "chemical": "Copper fungicide / Mancozeb",
        "organic": "Neem oil + Bordeaux mixture",
        "steps": [
            "Remove and destroy infected plant parts",
            "Apply copper-based fungicide every 7 days",
            "Avoid overhead irrigation",
            "Improve air circulation around plants",
        ],
        "prevention": "Use disease-resistant varieties, practice crop rotation",
    },
    "Early Blight": {
        "crop": ["Tomato", "Potato"],
        "chemical": "Chlorothalonil / Azoxystrobin",
        "organic": "Neem oil spray",
        "steps": [
            "Remove lower infected leaves",
            "Apply neem oil every 10 days",
            "Mulch around base to reduce soil splash",
            "Apply balanced fertilizer to strengthen plant",
        ],
        "prevention": "Crop rotation, remove plant debris after harvest",
    },
    "Leaf Blast": {
        "crop": ["Rice"],
        "chemical": "Tricyclazole / Isoprothiolane",
        "organic": "Silicon-rich soil amendment",
        "steps": [
            "Apply tricyclazole fungicide at first sign",
            "Reduce excess nitrogen fertilizer",
            "Maintain proper water levels (avoid drought stress)",
            "Remove heavily infected tillers",
        ],
        "prevention": "Use blast-resistant varieties, balanced N fertilization",
    },
    "Apple Scab": {
        "crop": ["Apple"],
        "chemical": "Captan / Myclobutanil",
        "organic": "Sulfur spray",
        "steps": [
            "Apply captan fungicide at bud break",
            "Remove and destroy fallen infected leaves",
            "Prune for better airflow inside canopy",
            "Spray every 7-10 days during wet weather",
        ],
        "prevention": "Plant resistant varieties, avoid overhead watering",
    },
    "Stripe Rust": {
        "crop": ["Wheat"],
        "chemical": "Propiconazole / Tebuconazole",
        "organic": "Sulfur-based spray",
        "steps": [
            "Apply fungicide at first sign of yellow stripes",
            "Scout fields weekly during cool wet weather",
            "Ensure balanced nutrition (avoid excess N)",
            "Remove volunteer wheat from nearby areas",
        ],
        "prevention": "Plant resistant varieties, early sowing",
    },
    "Leaf Rust": {
        "crop": ["Wheat"],
        "chemical": "Trifloxystrobin / Epoxiconazole",
        "organic": "Neem-based spray",
        "steps": [
            "Apply systemic fungicide at flag leaf stage",
            "Remove heavily infected plants",
            "Maintain field hygiene after harvest",
        ],
        "prevention": "Use certified rust-resistant seed varieties",
    },
    "Northern Leaf Blight": {
        "crop": ["Corn"],
        "chemical": "Azoxystrobin / Propiconazole",
        "organic": "Compost tea spray",
        "steps": [
            "Apply foliar fungicide at V8 growth stage",
            "Rotate with non-host crops",
            "Till crop residues to reduce inoculum",
        ],
        "prevention": "Use resistant hybrids, crop rotation with soybean",
    },
    "Gray Leaf Spot": {
        "crop": ["Corn"],
        "chemical": "Pyraclostrobin / Flutriafol",
        "organic": "Copper-based spray",
        "steps": [
            "Apply fungicide before tasseling",
            "Reduce crop residue on surface",
            "Maintain adequate plant spacing for airflow",
        ],
        "prevention": "Resistant hybrids, minimum tillage adjustment",
    },
    "Black Rot": {
        "crop": ["Grape"],
        "chemical": "Myclobutanil / Mancozeb",
        "organic": "Bordeaux mixture",
        "steps": [
            "Remove mummified berries from vines",
            "Apply fungicide from bud break through veraison",
            "Prune to improve airflow",
        ],
        "prevention": "Good canopy management, remove infected debris promptly",
    },
}


# ============================================================
# IMAGE QUALITY CHECK
# ============================================================

def image_quality_score(image_bytes):

    img_array = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_GRAYSCALE)

    if img is None:
        return {
            "good_quality": False
        }

    blur = cv2.Laplacian(img, cv2.CV_64F).var()
    brightness = np.mean(img)

    return {
        "blur_score": round(float(blur), 2),
        "brightness": round(float(brightness), 2),
        "good_quality": blur > 25 and 20 < brightness < 240
    }


# ============================================================
# LESION SEGMENTATION
# ============================================================

def extract_lesion_features(image_bytes):

    img_array = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    if img is None:
        return {}

    img = cv2.resize(img, (512, 512))

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    lower_brown = np.array([5, 40, 20])
    upper_brown = np.array([35, 255, 200])

    mask = cv2.inRange(hsv, lower_brown, upper_brown)

    kernel = np.ones((5, 5), np.uint8)

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        kernel
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel
    )

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    lesion_count = 0
    lesion_areas = []
    irregularity_scores = []

    for cnt in contours:

        area = cv2.contourArea(cnt)

        if area < 25:
            continue

        lesion_count += 1
        lesion_areas.append(area)

        perimeter = cv2.arcLength(cnt, True)

        if perimeter > 0:
            circularity = (
                4 * np.pi * area
            ) / (perimeter * perimeter)

            irregularity = 1 - circularity

            irregularity_scores.append(irregularity)

    avg_lesion_area = (
        np.mean(lesion_areas)
        if lesion_areas else 0
    )

    avg_irregularity = (
        np.mean(irregularity_scores)
        if irregularity_scores else 0
    )

    return {
        "lesion_count": lesion_count,
        "avg_lesion_area": round(float(avg_lesion_area), 2),
        "avg_irregularity": round(float(avg_irregularity), 3),
        "severe_lesion_load":
            bool(lesion_count > 20 and avg_lesion_area > 100)
    }


# ============================================================
# COLOR + TEXTURE EXTRACTION
# ============================================================

def extract_image_features(image_bytes):

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    small = img.resize((128, 128))

    pixels = list(small.getdata())

    total = len(pixels)

    green = 0
    brown = 0
    yellow = 0
    necrotic = 0
    orange = 0
    white = 0

    for r, g, b in pixels:

        if g > r and g > b and g > 80:
            green += 1

        elif r > 100 and g > 60 and b < 60:
            brown += 1

        elif r > 150 and g > 150 and b < 100:
            yellow += 1

        elif r < 70 and g < 70 and b < 70:
            necrotic += 1

        elif r > 160 and 80 < g < 150:
            orange += 1

        elif r > 200 and g > 200 and b > 200:
            white += 1

    gray = small.convert("L")

    edges = gray.filter(ImageFilter.FIND_EDGES)

    edge_pixels = list(edges.getdata())

    edge_density = (
        sum(1 for p in edge_pixels if p > 50)
        / len(edge_pixels)
    ) * 100

    features = {
        "green_pct": round(green / total * 100, 2),
        "brown_pct": round(brown / total * 100, 2),
        "yellow_pct": round(yellow / total * 100, 2),
        "necrotic_pct": round(necrotic / total * 100, 2),
        "orange_pct": round(orange / total * 100, 2),
        "white_pct": round(white / total * 100, 2),
        "edge_density": round(edge_density, 2)
    }

    lesion_features = extract_lesion_features(image_bytes)

    features.update(lesion_features)

    return features


# ============================================================
# CROP DISEASE RULES
# ============================================================

CROP_DISEASE_RULES = {

    "Tomato": {

        "Late Blight": {
            "min_necrotic": 8,
            "min_irregularity": 0.35,
            "min_lesions": 10
        },

        "Early Blight": {
            "min_brown": 10,
            "min_lesions": 6
        }
    },

    "Rice": {

        "Leaf Blast": {
            "min_necrotic": 5,
            "min_lesions": 15
        }
    },

    "Apple": {

        "Apple Scab": {
            "min_lesions": 12,
            "min_irregularity": 0.3
        }
    }
}


# ============================================================
# VALIDATE DISEASE
# ============================================================

def validate_disease_prediction(
    crop,
    disease,
    features
):

    rules = (
        CROP_DISEASE_RULES
        .get(crop, {})
        .get(disease)
    )

    if not rules:
        return True

    if (
        features.get("necrotic_pct", 0)
        < rules.get("min_necrotic", 0)
    ):
        return False

    if (
        features.get("brown_pct", 0)
        < rules.get("min_brown", 0)
    ):
        return False

    if (
        features.get("lesion_count", 0)
        < rules.get("min_lesions", 0)
    ):
        return False

    if (
        features.get("avg_irregularity", 0)
        < rules.get("min_irregularity", 0)
    ):
        return False

    return True


# ============================================================
# REAL CONFIDENCE
# ============================================================

def compute_real_confidence(
    features,
    disease_found
):

    confidence = 40

    if features.get("lesion_count", 0) > 10:
        confidence += 15

    if features.get("necrotic_pct", 0) > 8:
        confidence += 15

    if features.get("avg_irregularity", 0) > 0.3:
        confidence += 10

    if disease_found:
        confidence += 10

    return min(confidence, 96)


# ============================================================
# CROP ARCHETYPES — multi-feature prototype scoring
# Each entry defines the EXPECTED feature ranges for that crop.
# Fields: (min_green, max_green, min_yellow, max_yellow,
#          min_brown, max_brown, min_edge, max_edge,
#          min_necrotic, max_necrotic)
# ============================================================

CROP_ARCHETYPES = {
    # Tomato: broad leaves, moderate-high green, moderate edge
    "Tomato":  {"green": (35, 90), "yellow": (0, 20), "brown": (0, 25), "edge": (10, 30), "necrotic": (0, 20)},
    # Rice: very high green, long narrow leaves, moderate edge
    "Rice":    {"green": (55, 95), "yellow": (0, 15), "brown": (0, 10), "edge": (8, 25),  "necrotic": (0, 10)},
    # Wheat: yellowish-green stalks + grain, often golden/yellow,
    #        HIGH edge density from stalk texture, lower pure-green
    "Wheat":   {"green": (10, 60), "yellow": (5, 50), "brown": (0, 30), "edge": (18, 60), "necrotic": (0, 20)},
    # Corn: large broad leaves, high green, lower edge density
    "Corn":    {"green": (40, 90), "yellow": (0, 25), "brown": (0, 15), "edge": (3, 18),  "necrotic": (0, 10)},
    # Apple: moderately green, smooth leaves, lower edge
    "Apple":   {"green": (30, 80), "yellow": (0, 20), "brown": (0, 20), "edge": (5, 22),  "necrotic": (0, 15)},
    # Potato: dark-green broad leaves, medium edge
    "Potato":  {"green": (40, 85), "yellow": (0, 20), "brown": (0, 20), "edge": (8, 28),  "necrotic": (0, 15)},
    # Grape: deeply lobed leaves, medium-high edge
    "Grape":   {"green": (30, 80), "yellow": (0, 25), "brown": (0, 20), "edge": (12, 35), "necrotic": (0, 15)},
}


# ============================================================
# DYNAMIC CROP IDENTIFICATION — prototype scoring
# ============================================================

def identify_crop(features, hint: str = None):
    """Return the best-matching crop name based on image features.

    If `hint` is provided and is a known crop, it is used directly
    (the caller has already told us what crop was selected in the UI).
    Otherwise we score every archetype and pick the winner.
    """

    # ── honour explicit user hint ──────────────────────────────
    if hint and hint in CROP_ARCHETYPES:
        return hint

    green    = features.get("green_pct", 0)
    yellow   = features.get("yellow_pct", 0)
    brown    = features.get("brown_pct", 0)
    edge     = features.get("edge_density", 0)
    necrotic = features.get("necrotic_pct", 0)

    best_crop  = "Unknown"
    best_score = -1

    for crop, ranges in CROP_ARCHETYPES.items():

        score = 0

        # +1 for each feature that falls inside the expected range
        def in_range(val, lo, hi):
            return lo <= val <= hi

        if in_range(green,    *ranges["green"]):   score += 2   # green is most discriminative
        if in_range(yellow,   *ranges["yellow"]):  score += 1
        if in_range(brown,    *ranges["brown"]):   score += 1
        if in_range(edge,     *ranges["edge"]):    score += 2   # edge density also discriminative
        if in_range(necrotic, *ranges["necrotic"]): score += 1

        # Partial credit: how close the value is to the midpoint of the range
        def midpoint_closeness(val, lo, hi):
            mid = (lo + hi) / 2.0
            span = max(hi - lo, 1)
            return max(0.0, 1.0 - abs(val - mid) / span)

        score += midpoint_closeness(green,  *ranges["green"])  * 0.5
        score += midpoint_closeness(edge,   *ranges["edge"])   * 0.5
        score += midpoint_closeness(yellow, *ranges["yellow"]) * 0.3

        if score > best_score:
            best_score = score
            best_crop  = crop

    return best_crop



# ============================================================
# DISEASE DETECTION ENGINE
# ============================================================

def detect_disease(crop, features):

    brown        = features.get("brown_pct", 0)
    necrotic     = features.get("necrotic_pct", 0)
    lesions      = features.get("lesion_count", 0)
    irregularity = features.get("avg_irregularity", 0)
    yellow       = features.get("yellow_pct", 0)
    orange       = features.get("orange_pct", 0)

    # ========================================================
    # TOMATO
    # ========================================================

    if crop == "Tomato":

        if necrotic > 8 and lesions > 10 and irregularity > 0.35:
            return "Late Blight"

        if brown > 10 and lesions > 6:
            return "Early Blight"

    # ========================================================
    # RICE
    # ========================================================

    if crop == "Rice":

        if necrotic > 5 and lesions > 15:
            return "Leaf Blast"

    # ========================================================
    # APPLE
    # ========================================================

    if crop == "Apple":

        if lesions > 12 and irregularity > 0.3:
            return "Apple Scab"

    # ========================================================
    # WHEAT — rust diseases appear as orange/yellow pustules
    # ========================================================

    if crop == "Wheat":

        # Stripe rust: yellow streaks along leaf veins
        if yellow > 8 and lesions > 5:
            return "Stripe Rust"

        # Leaf rust: orange-brown circular pustules
        if (orange + brown) > 10 and lesions > 4:
            return "Leaf Rust"

        # Severe necrosis
        if necrotic > 12:
            return "Leaf Blight"

    # ========================================================
    # CORN / MAIZE
    # ========================================================

    if crop == "Corn":

        if necrotic > 10 and lesions > 8:
            return "Northern Leaf Blight"

        if brown > 15:
            return "Gray Leaf Spot"

    # ========================================================
    # POTATO
    # ========================================================

    if crop == "Potato":

        if necrotic > 8 and lesions > 10 and irregularity > 0.3:
            return "Late Blight"

        if brown > 8 and lesions > 5:
            return "Early Blight"

    # ========================================================
    # GRAPE
    # ========================================================

    if crop == "Grape":

        if brown > 10 and lesions > 8:
            return "Black Rot"

        if necrotic > 6 and irregularity > 0.3:
            return "Leaf Spot"

    return None



# ============================================================
# MAIN ANALYSIS  —  Llama Vision → pixel classifier fallback
# ============================================================

async def analyze_crop_image(image_base64, crop_hint: str = None):

    image_bytes = base64.b64decode(image_base64)

    # ── Quality gate ────────────────────────────────────────
    quality = image_quality_score(image_bytes)
    if not quality["good_quality"]:
        return {
            "success": False,
            "message": "Low quality image. Please use a clearer, well-lit crop photo."
        }

    # ── PRIMARY: OpenCV Semantic Extraction + Llama 3.1 8b ─
    # Tries the local text-only AI first; falls back to legacy pixel classifier if it fails.
    try:
        from app.feature_extraction import get_semantic_features
        from app.llama_text import analyze_with_llama_text
        
        # 1. Extract semantics using OpenCV
        semantics = get_semantic_features(image_bytes)
        
        # 2. Feed structured JSON semantics to Llama 3.1
        llama_result = analyze_with_llama_text(semantics, crop_hint=crop_hint)
    except Exception as e:
        print(f"[LlamaText] import/call error: {e}")
        llama_result = None

    if llama_result:
        crop = llama_result.get("crop_detected", "Unknown")

        # Enrich growth_needs from CROP_LIFECYCLE if Llama didn't give one
        if not llama_result.get("growth_needs"):
            lc = CROP_LIFECYCLE.get(crop, {})
            stages = lc.get("stages", [])
            water  = lc.get("water_needs", [])
            llama_result["growth_needs"] = (
                f"{crop} stages: {', '.join(stages)}. "
                f"Water needs: {water[0] if water else 'N/A'} → {water[-1] if water else 'N/A'}."
            ) if stages else f"Maintain optimal care for {crop}."

        # Add backward-compat fields expected by main.py
        disease = llama_result.get("disease", "Healthy")
        llama_result.update({
            "success":       True,
            "crop":          crop,
            "disease":       disease,
            "confidence":    llama_result.get("ai_confidence", 75),
            "recommendation": llama_result.get("recommendations", []),
            "quality":       _sanitise(quality),
        })
        print(f"[LlamaText] ✅ {crop} — {disease} ({llama_result['ai_confidence']:.0f}%)")
        return llama_result

    # ── FALLBACK: pixel-based classifier ────────────────────
    print("[LlamaText] ⚠️ Falling back to pixel classifier")
    features = extract_image_features(image_bytes)
    crop     = identify_crop(features, hint=crop_hint)
    disease  = detect_disease(crop, features)

    if disease:
        valid = validate_disease_prediction(crop, disease, features)
        if not valid:
            disease = None

    if disease:
        severity = "critical" if features["necrotic_pct"] > 15 else "warning"
    else:
        severity = "healthy"

    confidence = compute_real_confidence(features, disease is not None)
    recommendations = get_recommendation(crop, disease)

    if disease:
        health_assessment = (
            f"{crop} shows signs of {disease}. "
            f"Severity: {severity.upper()}. Immediate action recommended."
        )
        issues = [{
            "name": disease,
            "description": (
                f"Detected {disease}. Brown: {features.get('brown_pct', 0):.1f}%, "
                f"Necrotic: {features.get('necrotic_pct', 0):.1f}%, "
                f"Lesions: {features.get('lesion_count', 0)}."
            )
        }]
    else:
        health_assessment = (
            f"{crop} appears healthy with no visible disease. "
            "Continue regular monitoring and good agricultural practices."
        )
        issues = []

    lc = CROP_LIFECYCLE.get(crop, {})
    stages = lc.get("stages", [])
    water  = lc.get("water_needs", [])
    growth_needs = (
        f"{crop} stages: {', '.join(stages)}. "
        f"Water: {water[0] if water else 'N/A'} → {water[-1] if water else 'N/A'}."
    ) if stages else f"Maintain optimal care for {crop}."

    return {
        "crop_detected":     crop,
        "health_assessment": health_assessment,
        "issues":            issues,
        "recommendations":   recommendations,
        "growth_needs":      growth_needs,
        "severity":          severity,
        "ai_confidence":     float(confidence),
        "success":           True,
        "crop":              crop,
        "disease":           disease if disease else "Healthy",
        "confidence":        float(confidence),
        "recommendation":    recommendations,
        "features":          _sanitise(features),
        "quality":           _sanitise(quality),
        "_model":            "pixel-classifier-fallback",
    }




# ============================================================
# RECOMMENDATIONS
# ============================================================

def get_recommendation(crop, disease):

    if disease == "Late Blight":

        return [
            "Apply copper fungicide immediately",
            "Remove infected leaves",
            "Avoid overhead watering",
            "Increase air circulation",
            "Use Mancozeb spray every 7 days"
        ]

    if disease == "Early Blight":

        return [
            "Apply neem oil spray",
            "Remove infected leaves",
            "Use crop rotation",
            "Apply balanced fertilizer"
        ]

    if disease == "Leaf Blast":

        return [
            "Apply tricyclazole fungicide",
            "Reduce excess nitrogen",
            "Maintain proper water levels"
        ]

    if disease == "Apple Scab":

        return [
            "Apply captan fungicide",
            "Destroy fallen leaves",
            "Prune for better airflow"
        ]

    return [
        "Plant appears healthy",
        "Continue regular monitoring",
        "Maintain proper irrigation",
        "Use balanced nutrients"
    ]