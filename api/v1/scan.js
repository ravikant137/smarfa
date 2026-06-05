export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ success: false, message: 'Method Not Allowed' });

  const { image_base64, crop_hint } = req.body;
  if (!image_base64) return res.status(400).json({ success: false, message: 'image_base64 is required' });

  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) return res.status(500).json({ success: false, message: 'OpenAI API key not configured' });

  let prompt = `You are an agricultural plant disease expert. Analyze the uploaded crop image carefully.
Return ONLY a valid JSON object matching this structure exactly:
{
  "crop_detected": "Crop name",
  "disease": "Disease name (or 'Healthy')",
  "confidence": 95.0,
  "severity": "healthy", "warning", or "critical",
  "health_assessment": "Symptoms observed. If uncertain, say uncertain. Do not hallucinate.",
  "recommendations": [
    "Recommended pesticide: ...",
    "Organic treatment: ...",
    "Prevention methods: ..."
  ]
}`;

  if (crop_hint) prompt += `\nHint: The farmer suspects this is a ${crop_hint} crop.`;

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
