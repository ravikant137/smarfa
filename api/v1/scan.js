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

Return ONLY a valid JSON object. Fill each field based on the actual image — do NOT copy the example values literally:
{
  "crop_detected": "Common Name (Scientific Name)",
  "plant_type": "one of: crop | fruit | flower | ornamental | herb | vegetable",
  "severity": "one of: healthy | warning | critical",
  "ai_confidence": 0.0,
  "health_assessment": "2-sentence summary of overall health.",
  "structured": {
    "final_crop": "Common plant name only",
    "plant_category": "Crop / Fruit / Flower / Ornamental / Herb / Vegetable",
    "disease": {
      "name": "Disease name or 'No disease detected'",
      "confidence": "High / Medium / Low",
      "cause": "Fungal / Bacterial / Viral / Pest / Nutrient Deficiency / Physiological",
      "severity": "Low / Medium / High / Critical"
    },
    "safety_check": {
      "verified": true,
      "chemical": "Active ingredient name only",
      "safety_class": "Organic / Synthetic / Restricted",
      "eco_status": "e.g. Safe for bees",
      "compliance_details": "Pre-harvest interval or local notes."
    },
    "treatment": {
      "organic": "Organic treatment steps.",
      "chemical": "ONLY THE INGREDIENT NAME — 1 to 3 words max, e.g. Tricyclazole or Copper Oxychloride or Neem Oil. NO sentences. NO dosage here.",
      "dosage": "Mixing ratio only, e.g. 0.6g per Liter of water.",
      "prevention": "Cultural prevention steps.",
      "irrigation_adjustment": "Increase / Decrease / Maintain.",
      "soil_correction": "Fertilizer or pH fix needed.",
      "flower_care": "Pruning or bloom tips if flower plant.",
      "fruit_care": "Ripening or harvest tips if fruit plant."
    },
    "product": {
      "commercial_name": "Most common Indian brand name for this treatment, e.g. Beam 75 WP or Dithane M-45",
      "active_ingredient": "Pure ingredient keyword only, e.g. Tricyclazole",
      "amazon_search_term": "Exact search term to find this product on Amazon India",
      "alternatives": ["Alternative Indian Brand 1", "Alternative Indian Brand 2"]
    },
    "agent_logs": {
      "pathology_agent": "Visual symptoms observed.",
      "agronomy_agent": "Environmental factors.",
      "safety_agent": "Safety precautions."
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
