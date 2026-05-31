import json
import re
import urllib.request
import urllib.error
from typing import Optional

LLAMA_TEXT_PROMPT = """You are an expert agricultural AI. You are given highly structured semantic visual data extracted from a crop image by a computer vision pipeline.

Analyze this data and respond ONLY with valid JSON exactly matching this structure:

{
  "crop_detected": "<Infer crop based on shape/data or use context hint>",
  "disease": "<specific disease name or 'Healthy'>",
  "severity": "<healthy|warning|critical>",
  "confidence": <0-100>,
  "health_assessment": "<Short 1-2 sentence summary of plant health based on the features>",
  "issues": [
    {
      "name": "<Symptom name>",
      "description": "<Very brief description based on the extracted features>"
    }
  ],
  "recommendations": [
    "<Short actionable step 1 - suggest fertilizers if applicable>",
    "<Short actionable step 2 - suggest pesticides if applicable>",
    "<Short actionable step 3 - preventive measures>"
  ],
  "growth_needs": "<Short care note>"
}

Rules:
1. ONLY return JSON.
2. Keep ALL text responses extremely short and concise (1-2 lines max).
3. If healthy, recommend basic maintenance.
4. Do NOT output any conversational text.

Visual Semantic Data:
"""

def analyze_with_llama_text(semantic_features: dict, crop_hint: Optional[str] = None) -> Optional[dict]:
    """
    Send semantic JSON to local llama3.1:8b text model and return structured result.
    """
    
    prompt = LLAMA_TEXT_PROMPT + json.dumps(semantic_features, indent=2)
    if crop_hint and crop_hint not in ("Auto Detect", ""):
        prompt += f"\n\nContext Hint: The farmer stated this is a {crop_hint} plant."

    payload = {
        "model": "llama3.1:8b",
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "keep_alive": "1h",
        "options": {
            "temperature": 0.1,
            "num_predict": 300
        }
    }

    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read())
            raw = result.get("response", "").strip()

            json_match = re.search(r'\{[\s\S]*\}', raw)
            if not json_match:
                print(f"[LlamaText] No JSON in response: {raw[:200]}")
                return None

            data = json.loads(json_match.group())

            return {
                "crop_detected":     str(data.get("crop_detected", crop_hint if crop_hint else "Unknown")),
                "disease":           str(data.get("disease", "Healthy")),
                "severity":          str(data.get("severity", "healthy")).lower(),
                "ai_confidence":     float(data.get("confidence", 70)),
                "health_assessment": str(data.get("health_assessment", "")),
                "issues":            list(data.get("issues", [])),
                "recommendations":   list(data.get("recommendations", [])),
                "growth_needs":      str(data.get("growth_needs", "")),
                "_model":            "local-llama-3.1-8b-text",
            }

    except Exception as e:
        print(f"[LlamaText] API error: {e}")
        return None
