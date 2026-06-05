export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ success: false, message: 'Method Not Allowed' });

  const { image_base64, crop_hint } = req.body;
  if (!image_base64) return res.status(400).json({ success: false, message: 'image_base64 is required' });

  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) return res.status(500).json({ success: false, message: 'OpenAI API key not configured' });

  let prompt = `You are an expert Plant & Agricultural AI Assistant with deep knowledge of crops, fruits, flowers, and ornamental plants.
Analyze the uploaded plant image in incredible detail using a structured diagnostic approach.

CRITICAL INSTRUCTIONS:
1. You MUST identify the exact plant type — whether it is a CROP (wheat, rice, corn), a FRUIT plant (mango, papaya, strawberry, watermelon), a FLOWER/ORNAMENTAL plant (rose, marigold, jasmine, sunflower, hibiscus), or any other plant.
2. Do NOT confuse plant types. Look closely at leaf shape, flower colour, stem structure, fruit presence, and growth form.
3. Identify diseases, pests, and nutrient deficiencies specific to that plant type.
4. If the image shows a flower plant, provide flower-specific disease and care advice.
5. If the image shows a fruit plant, provide fruit-specific disease, ripening, and harvest advice.
6. If you are unsure of the species, state the most probable genus. Only use 'Unknown Plant' as a last resort.

Return ONLY a valid JSON object matching this EXACT structure:
{
  "crop_detected": "Common Name (Scientific Name) — e.g. Rose (Rosa indica) or Papaya (Carica papaya)",
  "plant_type": "crop", "fruit", "flower", or "ornamental",
  "severity": "healthy", "warning", or "critical",
  "ai_confidence": 95.5,
  "health_assessment": "High-level summary of the plant's health and appearance.",
  "structured": {
    "confidence_warning": "Include ONLY if image is blurry or hard to identify, else omit.",
    "final_crop": "Common Plant Name",
    "plant_category": "Crop / Fruit / Flower / Ornamental / Herb / Vegetable",
    "disease": {
      "name": "Disease Name or 'No disease detected'",
      "confidence": "High / Medium / Low",
      "cause": "Fungal, Bacterial, Viral, Pest, Nutrient Deficiency, or Physiological",
      "severity": "Low, Medium, High, or Critical"
    },
    "safety_check": {
      "verified": true,
      "chemical": "Name of recommended active ingredient",
      "safety_class": "Organic / Synthetic / Restricted",
      "eco_status": "Safe for bees / Toxic to fish / etc.",
      "compliance_details": "Local regulatory notes or pre-harvest intervals."
    },
    "treatment": {
      "organic": "Step-by-step organic/natural treatment.",
      "chemical": "Targeted chemical treatment if necessary.",
      "dosage": "Exact mixing ratios (e.g. 2ml per Liter of water).",
      "prevention": "Cultural practices to stop recurrence.",
      "irrigation_adjustment": "Should water be increased or decreased?",
      "soil_correction": "Fertilizer or pH changes needed.",
      "flower_care": "For flower plants: pruning, deadheading, bloom boosting tips.",
      "fruit_care": "For fruit plants: thinning, ripening, post-harvest tips."
    },
    "agent_logs": {
      "pathology_agent": "Detailed visual symptoms observed (lesions, chlorosis, wilting, spots, etc).",
      "agronomy_agent": "Environmental factors likely contributing to this condition.",
      "safety_agent": "Safety precautions for the farmer or gardener."
    }
  }
}`;

  if (crop_hint) prompt += `\nHint: The user suspects this is a ${crop_hint} plant.`;

  try {
    const payload = {
      model: "gpt-4o",
      messages: [
        {
          role: "user",
          content: [
            { type: "text", text: prompt },
            { type: "image_url", image_url: { url: `data:image/jpeg;base64,${image_base64}` } }
          ]
        }
      ],
      response_format: { type: "json_object" },
      temperature: 0.2
    };

    const response = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${apiKey}`
      },
      body: JSON.stringify(payload)
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.error?.message || 'OpenAI API error');

    const resultStr = data.choices[0].message.content;
    const resultJson = JSON.parse(resultStr);

    res.status(200).json({ success: true, data: resultJson });
  } catch (error) {
    console.error("GPT API Error:", error);
    res.status(500).json({ success: false, message: error.message || 'AI processing failed' });
  }
}
