"""
Crop image analysis using FREE AI — no API keys required.

Pipeline:
  1. Ollama + LLaVA (local vision LLM — free, private, no API key)
     → Install: https://ollama.com  then run: ollama pull llava
  2. Local PIL-based color analysis (always works, no install needed)
  3. Agricultural knowledge base for expert recommendations
"""

import base64
import io
import os
import json
import logging

logger = logging.getLogger(__name__)

OLLAMA_BASE = os.getenv("OLLAMA_HOST", "http://localhost:11434")


# ── Agricultural Knowledge Base ───────────────────────────────────────────
DISEASE_KNOWLEDGE = {
    "Tomato___Late_blight": {
        "crop": "Tomato",
        "disease": "Late Blight",
        "severity": "critical",
        "description": "Caused by Phytophthora infestans. Dark, water-soaked lesions on leaves and stems that rapidly enlarge. White mold may appear on leaf undersides in humid conditions.",
        "recommendations": [
            "Remove and destroy all infected plant material immediately.",
            "Apply copper-based fungicide (Bordeaux mixture) as preventive spray.",
            "Improve air circulation by proper spacing (60-90cm between plants).",
            "Avoid overhead irrigation; use drip irrigation instead.",
            "Apply chlorothalonil or mancozeb fungicide every 7-10 days during wet weather.",
        ],
        "growth_needs": "Tomatoes need full sun (8+ hours), well-drained soil with pH 6.0-6.8, consistent moisture (1-2 inches/week), and temperatures between 21-29°C.",
    },
    "Tomato___Early_blight": {
        "crop": "Tomato",
        "disease": "Early Blight",
        "severity": "warning",
        "description": "Caused by Alternaria solani. Concentric ring-shaped brown spots on older leaves, starting from the bottom of the plant. Leaves yellow and drop prematurely.",
        "recommendations": [
            "Remove lower infected leaves to prevent spread upward.",
            "Mulch around base to prevent soil splash onto leaves.",
            "Apply neem oil or copper fungicide every 7-14 days.",
            "Rotate crops — don't plant tomatoes in the same spot for 3 years.",
            "Ensure adequate potassium levels in soil to strengthen plant immunity.",
        ],
        "growth_needs": "Maintain consistent watering schedule, avoid wetting foliage. Feed with balanced fertilizer (10-10-10) every 2 weeks.",
    },
    "Tomato___Bacterial_spot": {
        "crop": "Tomato",
        "disease": "Bacterial Spot",
        "severity": "warning",
        "description": "Caused by Xanthomonas bacteria. Small, dark, raised spots on leaves, stems and fruit. Leaves may yellow and drop.",
        "recommendations": [
            "Remove and destroy infected plants to prevent bacterial spread.",
            "Apply copper-based bactericide as preventive measure.",
            "Use disease-free seed and transplants.",
            "Avoid working with wet plants to reduce spread.",
            "Practice crop rotation with non-solanaceous crops.",
        ],
        "growth_needs": "Keep foliage dry, improve air circulation, maintain soil pH 6.2-6.8, provide consistent irrigation.",
    },
    "Tomato___Septoria_leaf_spot": {
        "crop": "Tomato",
        "disease": "Septoria Leaf Spot",
        "severity": "warning",
        "description": "Caused by Septoria lycopersici. Small circular spots with dark borders and gray centers on lower leaves. Tiny black dots (pycnidia) visible in spot centers.",
        "recommendations": [
            "Remove infected lower leaves immediately.",
            "Apply chlorothalonil or copper-based fungicide.",
            "Mulch to prevent soil splash.",
            "Water at soil level, not overhead.",
            "Ensure proper plant spacing for air circulation.",
        ],
        "growth_needs": "Good drainage, consistent moisture without leaf wetness, balanced nutrition with emphasis on calcium.",
    },
    "Tomato___healthy": {
        "crop": "Tomato",
        "disease": None,
        "severity": "healthy",
        "description": "The tomato plant appears healthy with good leaf color and structure. No visible signs of disease or pest damage.",
        "recommendations": [
            "Continue regular watering schedule: 1-2 inches per week at soil level.",
            "Apply balanced fertilizer (10-10-10) every 2-3 weeks during growing season.",
            "Monitor for early signs of pests — check leaf undersides weekly.",
            "Stake or cage plants for proper support as fruit develops.",
            "Prune suckers to improve air circulation and fruit production.",
        ],
        "growth_needs": "Full sun 8+ hours, soil pH 6.0-6.8, consistent moisture, temperature 21-29°C, potassium-rich feed during fruiting.",
    },
    "Potato___Late_blight": {
        "crop": "Potato",
        "disease": "Late Blight",
        "severity": "critical",
        "description": "Same pathogen as tomato late blight. Dark water-soaked lesions, white fungal growth. Can destroy entire crop within days in cool wet conditions.",
        "recommendations": [
            "Destroy all infected foliage and tubers — do not compost.",
            "Apply preventive fungicide (mancozeb/chlorothalonil) during humid weather.",
            "Hill potatoes well to protect tubers from spore rain.",
            "Harvest on dry days and cure tubers before storage.",
            "Plant certified disease-free seed potatoes.",
        ],
        "growth_needs": "Cool climate (15-20°C), well-drained loose soil, consistent moisture, pH 5.0-6.0, high potassium during tuber formation.",
    },
    "Potato___Early_blight": {
        "crop": "Potato",
        "disease": "Early Blight",
        "severity": "warning",
        "description": "Target-shaped brown spots on older leaves. Premature defoliation reduces tuber yield significantly.",
        "recommendations": [
            "Remove and destroy infected lower leaves.",
            "Apply fungicide containing azoxystrobin or chlorothalonil.",
            "Ensure adequate nitrogen and phosphorus nutrition.",
            "Practice 3-year crop rotation.",
            "Irrigate in morning so foliage dries during the day.",
        ],
        "growth_needs": "Balanced NPK fertilizer, consistent soil moisture, good air circulation, avoid overhead watering.",
    },
    "Potato___healthy": {
        "crop": "Potato",
        "disease": None,
        "severity": "healthy",
        "description": "The potato plant appears healthy with vigorous green foliage. Good prospects for tuber development.",
        "recommendations": [
            "Continue hilling soil around stems as plants grow.",
            "Maintain consistent watering — 1-2 inches per week.",
            "Apply potassium-rich fertilizer as plants approach flowering.",
            "Monitor for Colorado potato beetle and aphids weekly.",
            "Plan harvest 2-3 weeks after foliage dies back naturally.",
        ],
        "growth_needs": "Cool temperatures (15-20°C), loose well-drained soil, pH 5.0-6.0, steady moisture, high potassium during tuber fill.",
    },
    "Corn___Common_rust": {
        "crop": "Corn",
        "disease": "Common Rust",
        "severity": "warning",
        "description": "Caused by Puccinia sorghi. Small round to elongated cinnamon-brown pustules on both leaf surfaces. Severe infections reduce photosynthesis.",
        "recommendations": [
            "Plant rust-resistant hybrid varieties.",
            "Apply foliar fungicide (triazole-based) if infection is early and severe.",
            "Ensure adequate plant spacing for air movement.",
            "Remove heavily infected leaves if practical.",
            "Rotate with non-grass crops to break disease cycle.",
        ],
        "growth_needs": "Full sun, deep well-drained soil, heavy nitrogen feeder — apply 200kg N/ha in splits, consistent water during tasseling.",
    },
    "Corn___Northern_Leaf_Blight": {
        "crop": "Corn",
        "disease": "Northern Leaf Blight",
        "severity": "warning",
        "description": "Caused by Exserohilum turcicum. Long elliptical gray-green lesions on leaves. Can cause significant yield loss if infection occurs before tasseling.",
        "recommendations": [
            "Plant resistant hybrids with Ht genes.",
            "Apply strobilurin fungicide at early tassel if disease pressure is high.",
            "Practice crop rotation — avoid corn-on-corn.",
            "Manage crop residue by tillage or decomposition.",
            "Ensure balanced fertility to strengthen plant defense.",
        ],
        "growth_needs": "Deep fertile soil, 500-800mm rainfall during growing season, warm temperatures 25-30°C, balanced NPK nutrition.",
    },
    "Corn___healthy": {
        "crop": "Corn",
        "disease": None,
        "severity": "healthy",
        "description": "The corn plant shows vigorous growth with good green color. Healthy leaf structure indicates adequate nutrition.",
        "recommendations": [
            "Apply side-dress nitrogen at V6-V8 stage for maximum yield.",
            "Ensure irrigation during silking and grain fill — critical water demand period.",
            "Scout for fall armyworm, corn borer, and aphids weekly.",
            "Maintain weed-free rows during first 6 weeks of growth.",
            "Plan harvest when kernels reach black layer stage (30% moisture).",
        ],
        "growth_needs": "Heavy nitrogen needs (200-250 kg/ha), full sun, soil temp above 10°C for germination, 500-800mm water during season.",
    },
    "Rice___Brown_spot": {
        "crop": "Rice",
        "disease": "Brown Spot",
        "severity": "warning",
        "description": "Caused by Bipolaris oryzae. Oval brown spots on leaves with gray centers. Associated with nutrient-deficient soils, especially silicon and potassium.",
        "recommendations": [
            "Apply silicon-based fertilizer to strengthen cell walls.",
            "Correct potassium and manganese deficiencies in soil.",
            "Treat seed with fungicide before planting.",
            "Apply foliar fungicide (propiconazole) at boot stage.",
            "Maintain proper water level in paddy — not too deep or shallow.",
        ],
        "growth_needs": "Standing water 5-10cm during vegetative stage, soil pH 5.5-6.5, balanced NPK + silicon, warm temperatures 25-35°C.",
    },
    "Rice___Leaf_blast": {
        "crop": "Rice",
        "disease": "Leaf Blast",
        "severity": "critical",
        "description": "Caused by Magnaporthe oryzae. Diamond-shaped lesions with gray centers and brown borders on leaves. Can devastate entire fields rapidly.",
        "recommendations": [
            "Plant blast-resistant varieties appropriate for your region.",
            "Reduce nitrogen application — excess N increases susceptibility.",
            "Apply tricyclazole or isoprothiolane fungicide preventively.",
            "Maintain adequate but not excessive water levels.",
            "Avoid late planting which increases blast risk.",
        ],
        "growth_needs": "Controlled flooding, moderate nitrogen (avoid excess), silicon supplementation, temperatures 24-28°C ideal for healthy growth.",
    },
    "Grape___Black_rot": {
        "crop": "Grape",
        "disease": "Black Rot",
        "severity": "critical",
        "description": "Caused by Guignardia bidwellii. Reddish-brown circular leaf spots, fruit becomes hard black mummies. Most destructive grape disease in humid regions.",
        "recommendations": [
            "Remove and destroy all mummified fruit and infected material.",
            "Apply fungicide (myclobutanil or mancozeb) from bud break through veraison.",
            "Maintain open canopy through pruning for air circulation.",
            "Remove wild grapes near vineyard which harbor the pathogen.",
            "Spray program: start at 10-inch shoot growth, repeat every 10-14 days.",
        ],
        "growth_needs": "Full sun, well-drained soil pH 5.5-6.5, annual pruning, balanced K and Ca nutrition, 600-800mm annual rainfall.",
    },
    "Apple___Apple_scab": {
        "crop": "Apple",
        "disease": "Apple Scab",
        "severity": "warning",
        "description": "Caused by Venturia inaequalis. Olive-green to brown velvety spots on leaves and fruit. Severely infected leaves curl and drop early.",
        "recommendations": [
            "Rake and destroy fallen leaves in autumn to reduce overwintering spores.",
            "Apply fungicide (captan or myclobutanil) from green tip through petal fall.",
            "Plant scab-resistant varieties where possible.",
            "Prune for open canopy to improve air circulation.",
            "Apply urea spray (5%) to fallen leaves in autumn to speed decomposition.",
        ],
        "growth_needs": "Full sun, well-drained soil, pH 6.0-7.0, annual pruning, balanced NPK with calcium, chill hours 800-1200.",
    },
    "Wheat___healthy": {
        "crop": "Wheat",
        "disease": None,
        "severity": "healthy",
        "description": "The wheat crop appears healthy with good tiller development and green coloration.",
        "recommendations": [
            "Apply top-dress nitrogen at tillering and stem elongation stages.",
            "Monitor for aphids, Hessian fly, and rust diseases weekly.",
            "Maintain soil moisture during grain fill period — critical for yield.",
            "Scout for weeds and apply selective herbicide if needed.",
            "Plan harvest at 13-14% grain moisture content.",
        ],
        "growth_needs": "Cool-season crop (15-24°C), 300-500mm water during season, nitrogen-responsive, soil pH 6.0-7.0.",
    },
}

# Generic knowledge for unknown crops/diseases
GENERIC_KNOWLEDGE = {
    "healthy": {
        "severity": "healthy",
        "description": "The plant appears to be in good health based on visible characteristics. Leaf color, structure, and overall vigor look normal.",
        "recommendations": [
            "Continue current care regimen — watering, fertilizing, and pest monitoring.",
            "Test soil every 6 months to track nutrient levels and pH.",
            "Apply organic compost (2-3 inches) as mulch to improve soil health.",
            "Rotate crops each season to prevent soil-borne disease buildup.",
            "Keep records of planting dates, fertilizer applications, and yields.",
        ],
        "growth_needs": "Most crops need: 6-8 hours sunlight, consistent moisture (1-2 inches/week), soil pH 6.0-7.0, balanced NPK nutrition, good drainage.",
    },
    "diseased": {
        "severity": "warning",
        "description": "Signs of stress or disease detected. The plant shows symptoms that need attention to prevent further damage and yield loss.",
        "recommendations": [
            "Isolate affected plants to prevent disease spread to healthy crops.",
            "Take clear close-up photos and consult local agricultural extension office.",
            "Apply broad-spectrum organic fungicide (neem oil or copper-based) as first response.",
            "Check and correct irrigation — both over and under-watering cause disease.",
            "Test soil for nutrient deficiencies, especially nitrogen, potassium, and micronutrients.",
            "Improve air circulation by pruning and proper plant spacing.",
        ],
        "growth_needs": "Address soil health first. Ensure proper drainage, balanced pH (6.0-7.0), adequate organic matter. Reduce nitrogen if fungal disease is present.",
    },
}


def extract_image_features(image_bytes: bytes) -> dict:
    """Extract visual features from crop image using PIL."""
    from PIL import Image
    import statistics

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img_small = img.resize((100, 100))
    pixels = list(img_small.getdata())

    total = len(pixels)
    r_vals = [p[0] for p in pixels]
    g_vals = [p[1] for p in pixels]
    b_vals = [p[2] for p in pixels]

    green_pixels = sum(1 for r, g, b in pixels if g > r and g > b and g > 60)
    brown_pixels = sum(1 for r, g, b in pixels if r > g and r > 80 and g > 40 and b < g)
    yellow_pixels = sum(1 for r, g, b in pixels if r > 150 and g > 150 and b < 100)
    dark_pixels = sum(1 for r, g, b in pixels if r < 60 and g < 60 and b < 60)
    white_pixels = sum(1 for r, g, b in pixels if r > 200 and g > 200 and b > 200)

    return {
        "avg_r": round(statistics.mean(r_vals), 1),
        "avg_g": round(statistics.mean(g_vals), 1),
        "avg_b": round(statistics.mean(b_vals), 1),
        "green_pct": round(green_pixels / total * 100, 1),
        "brown_pct": round(brown_pixels / total * 100, 1),
        "yellow_pct": round(yellow_pixels / total * 100, 1),
        "dark_pct": round(dark_pixels / total * 100, 1),
        "white_pct": round(white_pixels / total * 100, 1),
        "width": img.width,
        "height": img.height,
    }


async def analyze_with_ollama(image_base64: str, features: dict) -> dict | None:
    """Use Ollama text LLM + PIL features for crop analysis. No API key needed."""
    import httpx

    # Try vision models first (if system has enough RAM) — short timeout since they crash on low RAM
    vision_models = ["moondream", "llava"]
    for model in vision_models:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "model": model,
                    "prompt": "Analyze this crop/plant image. Respond with JSON: {\"crop\":\"name\",\"disease\":\"name or null\",\"severity\":\"critical/warning/healthy\",\"description\":\"details\",\"recommendations\":[\"list of 5\"],\"growth_needs\":\"needs\"}",
                    "images": [image_base64],
                    "stream": False,
                    "options": {"temperature": 0.3},
                }
                response = await client.post(f"{OLLAMA_BASE}/api/generate", json=payload)
                response.raise_for_status()
                text = response.json().get("response", "").strip()
                start = text.find("{")
                end = text.rfind("}") + 1
                if start >= 0 and end > start:
                    result = json.loads(text[start:end])
                    logger.info("Ollama/%s vision analysis succeeded", model)
                    is_healthy = result.get("severity") == "healthy" or result.get("disease") is None
                    issues = []
                    if not is_healthy and result.get("disease"):
                        issues.append({"name": result["disease"], "description": result.get("description", "")})
                    return {
                        "crop_detected": result.get("crop", "Unknown"),
                        "severity": result.get("severity", "warning"),
                        "health_assessment": result.get("description", ""),
                        "issues": issues,
                        "recommendations": result.get("recommendations", []),
                        "growth_needs": result.get("growth_needs", ""),
                        "ai_confidence": 80,
                        "_model": f"ollama-{model}",
                    }
        except httpx.ConnectError:
            logger.info("Ollama not running at %s", OLLAMA_BASE)
            return None
        except Exception as e:
            logger.info("Ollama/%s vision failed (likely RAM): %s", model, str(e)[:100])
            continue

    # Fallback: use text-only LLM (tinyllama/phi3) with extracted color features
    text_models = ["phi3", "tinyllama"]
    feature_prompt = f"""You are an agricultural expert. Analyze these crop image color measurements and give a diagnosis.

GREEN: {features['green_pct']}%
BROWN: {features['brown_pct']}%
YELLOW: {features['yellow_pct']}%
DARK: {features['dark_pct']}%
WHITE: {features['white_pct']}%

Reply with ONLY this JSON, fill in every field:
{{"crop":"crop name","disease":"disease or none","severity":"healthy","description":"2 sentences about plant health based on colors","recommendations":["water regularly","check soil pH","apply fertilizer","inspect for pests","ensure sunlight"],"growth_needs":"key needs"}}"""

    for model in text_models:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "model": model,
                    "prompt": feature_prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 300},
                }
                response = await client.post(f"{OLLAMA_BASE}/api/generate", json=payload)
                response.raise_for_status()
                text = response.json().get("response", "").strip()
                logger.info("Ollama/%s raw response: %s", model, text[:300])
                # Extract JSON
                start = text.find("{")
                end = text.rfind("}") + 1
                if start >= 0 and end > start:
                    result = json.loads(text[start:end])
                    logger.info("Ollama/%s text analysis: crop=%s, disease=%s", model, result.get("crop"), result.get("disease"))

                    # Determine severity from features if LLM didn't set it well
                    severity = result.get("severity", "")
                    if severity not in ("healthy", "warning", "critical"):
                        if features["brown_pct"] > 30:
                            severity = "critical"
                        elif features["yellow_pct"] > 20 or features["brown_pct"] > 15:
                            severity = "warning"
                        else:
                            severity = "healthy"

                    disease = result.get("disease")
                    if disease and disease.lower() in ("none", "null", "n/a", "no disease"):
                        disease = None

                    is_healthy = severity == "healthy" or disease is None
                    issues = []
                    if not is_healthy and disease:
                        issues.append({"name": disease, "description": result.get("description", "")})

                    recs = result.get("recommendations", [])
                    if not recs or not isinstance(recs, list):
                        recs = _default_recommendations(features)

                    desc = result.get("description", "")
                    if not desc:
                        desc = _default_description(features)

                    return {
                        "crop_detected": result.get("crop", "Unknown") or "Unknown",
                        "severity": severity,
                        "health_assessment": desc,
                        "issues": issues,
                        "recommendations": recs[:5],
                        "growth_needs": result.get("growth_needs", "") or "Regular watering, balanced NPK fertilizer, adequate sunlight.",
                        "ai_confidence": 55,
                        "_model": f"ollama-{model}+pil",
                    }
        except httpx.ConnectError:
            return None
        except Exception as e:
            logger.warning("Ollama/%s text failed: %s", model, str(e)[:100])
            continue

    return None


def _default_description(features: dict) -> str:
    parts = []
    if features["green_pct"] > 50:
        parts.append(f"Healthy green foliage covering {features['green_pct']}% of the image.")
    if features["brown_pct"] > 10:
        parts.append(f"Brown areas ({features['brown_pct']}%) may indicate disease or necrosis.")
    if features["yellow_pct"] > 10:
        parts.append(f"Yellow patches ({features['yellow_pct']}%) may suggest nutrient deficiency.")
    if features["dark_pct"] > 10:
        parts.append(f"Dark spots ({features['dark_pct']}%) could indicate fungal infection.")
    return " ".join(parts) if parts else "Image analysis complete. Color distribution is within normal range."


def _default_recommendations(features: dict) -> list:
    recs = ["Water your crops regularly, especially during dry periods."]
    if features["yellow_pct"] > 10:
        recs.append("Apply nitrogen-rich fertilizer to address yellowing leaves.")
    if features["brown_pct"] > 10:
        recs.append("Remove affected brown/dead foliage and apply fungicide.")
    if features["dark_pct"] > 10:
        recs.append("Apply copper-based fungicide for potential fungal spots.")
    recs.extend([
        "Monitor soil pH — most crops prefer 6.0-7.0.",
        "Inspect leaves weekly for pest damage or disease progression.",
        "Ensure adequate spacing between plants for air circulation.",
    ])
    return recs[:5]


def analyze_with_pil(image_bytes: bytes) -> dict:
    """Local image analysis using PIL — works offline, no API needed.
    Analyzes color distribution to estimate plant health."""
    from PIL import Image
    import statistics

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img_small = img.resize((100, 100))
    pixels = list(img_small.getdata())

    total = len(pixels)
    r_vals = [p[0] for p in pixels]
    g_vals = [p[1] for p in pixels]
    b_vals = [p[2] for p in pixels]

    avg_r = statistics.mean(r_vals)
    avg_g = statistics.mean(g_vals)
    avg_b = statistics.mean(b_vals)

    # Count green-dominant pixels (healthy foliage indicator)
    green_pixels = sum(1 for r, g, b in pixels if g > r and g > b and g > 60)
    green_ratio = green_pixels / total

    # Count brown/yellow pixels (disease/stress indicator)
    brown_pixels = sum(1 for r, g, b in pixels if r > g and r > 80 and g > 40 and b < g)
    brown_ratio = brown_pixels / total

    # Count yellow pixels (nutrient deficiency indicator)
    yellow_pixels = sum(1 for r, g, b in pixels if r > 150 and g > 150 and b < 100)
    yellow_ratio = yellow_pixels / total

    # Count dark spots (potential fungal disease)
    dark_pixels = sum(1 for r, g, b in pixels if r < 60 and g < 60 and b < 60)
    dark_ratio = dark_pixels / total

    # Determine health status
    issues = []
    if green_ratio > 0.4:
        severity = "healthy"
        description = f"The plant shows strong green coloration ({green_ratio:.0%} green foliage detected), indicating good health and active photosynthesis."
        knowledge = GENERIC_KNOWLEDGE["healthy"]
    elif brown_ratio > 0.3:
        severity = "critical"
        description = f"Significant browning detected ({brown_ratio:.0%} of plant area). This may indicate late blight, bacterial infection, or severe drought stress."
        issues.append({"name": "Browning / Necrosis", "description": "Large areas of brown tissue. Could be fungal (blight), bacterial, or environmental stress."})
        knowledge = GENERIC_KNOWLEDGE["diseased"]
    elif yellow_ratio > 0.2:
        severity = "warning"
        description = f"Yellowing detected ({yellow_ratio:.0%} of foliage). May indicate nutrient deficiency (nitrogen, iron) or early disease stage."
        issues.append({"name": "Chlorosis (Yellowing)", "description": "Leaf yellowing suggests nitrogen deficiency, iron chlorosis, or early fungal infection."})
        knowledge = GENERIC_KNOWLEDGE["diseased"]
    elif dark_ratio > 0.15:
        severity = "warning"
        description = f"Dark spots detected ({dark_ratio:.0%} of area). Could indicate fungal disease or pest damage."
        issues.append({"name": "Dark Spots / Lesions", "description": "Dark areas may be fungal lesions, bacterial spots, or pest damage. Inspect closely."})
        knowledge = GENERIC_KNOWLEDGE["diseased"]
    else:
        severity = "warning"
        description = f"Image analysis inconclusive. Color profile: R={avg_r:.0f} G={avg_g:.0f} B={avg_b:.0f}. Green coverage: {green_ratio:.0%}."
        knowledge = GENERIC_KNOWLEDGE["diseased"]
        issues.append({"name": "Inconclusive Analysis", "description": "For best results, install Ollama (https://ollama.com) and run: ollama pull llava"})

    return {
        "crop_detected": "Unknown (local analysis)",
        "severity": severity,
        "health_assessment": description,
        "issues": issues,
        "recommendations": knowledge["recommendations"],
        "growth_needs": knowledge["growth_needs"],
        "ai_confidence": 30 if green_ratio > 0.4 else 20,
        "_model": "local-pil",
        "_color_stats": {
            "green_ratio": round(green_ratio, 3),
            "brown_ratio": round(brown_ratio, 3),
            "yellow_ratio": round(yellow_ratio, 3),
            "dark_ratio": round(dark_ratio, 3),
        },
    }


async def analyze_crop_image(image_base64: str) -> dict:
    """
    Analyze a crop image — completely free, no API keys needed.
    Pipeline: vision LLM → PIL analysis + text LLM enhancement → PIL-only.
    """
    image_bytes = base64.b64decode(image_base64)

    # Extract color features first (fast, always works)
    features = extract_image_features(image_bytes)

    # Try Ollama vision models (if system has enough RAM)
    result = await analyze_with_ollama(image_base64, features)
    if result:
        # Cross-reference with knowledge base for enhanced recommendations
        crop = result.get("crop_detected", "")
        for key, knowledge in DISEASE_KNOWLEDGE.items():
            if knowledge["crop"].lower() in crop.lower():
                if knowledge["disease"] and any(knowledge["disease"].lower() in str(i).lower() for i in result.get("issues", [])):
                    result["recommendations"] = knowledge["recommendations"]
                    result["growth_needs"] = knowledge["growth_needs"]
                    break
        return result

    # Build PIL-based result, then try to enhance description with text LLM
    pil_result = analyze_with_pil(image_bytes)

    # Try to add AI-generated description using text LLM
    ai_desc = await _get_llm_description(features)
    if ai_desc:
        pil_result["health_assessment"] = ai_desc
        pil_result["ai_confidence"] = 50
        pil_result["_model"] = f"pil+llm"

    return pil_result


async def _get_llm_description(features: dict) -> str | None:
    """Ask tinyllama for a natural language crop health description. Returns None on failure."""
    import httpx

    green, brown, yellow = features["green_pct"], features["brown_pct"], features["yellow_pct"]
    prompt = f"A farmer's crop image has {green}% green, {brown}% brown, {yellow}% yellow pixels. In 2-3 sentences, describe the plant health and what the farmer should do."

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{OLLAMA_BASE}/api/generate", json={
                "model": "tinyllama",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.5, "num_predict": 150},
            })
            r.raise_for_status()
            text = r.json().get("response", "").strip()
            # Clean up — take first 2-3 meaningful sentences
            sentences = [s.strip() for s in text.replace("\n", " ").split(".") if len(s.strip()) > 10]
            if sentences:
                return ". ".join(sentences[:3]) + "."
    except Exception as e:
        logger.info("LLM description unavailable: %s", str(e)[:80])
    return None
