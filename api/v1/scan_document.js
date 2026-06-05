export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ success: false, message: 'Method Not Allowed' });

  const { image_base64 } = req.body;
  if (!image_base64) return res.status(400).json({ success: false, message: 'image_base64 is required' });

  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) return res.status(500).json({ success: false, message: 'OpenAI API key not configured' });

  const prompt = `You are an expert agricultural assistant. Analyze the uploaded image of a document (e.g., pesticide label, fertilizer bag, prescription, or soil report).
Extract the key information and return ONLY a valid JSON object matching this exact structure:
{
  "document_type": "Type of document (e.g. Fertilizer Label)",
  "extracted_text": "A brief summary of the main text/instructions found on the label",
  "warnings": "Any safety warnings or precautions",
  "usage_instructions": "How to use the product, dosage, timing, etc.",
  "active_ingredients": "List of active ingredients"
}`;

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
      temperature: 0.1
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
    res.status(500).json({ success: false, message: error.message || 'Document extraction failed' });
  }
}
