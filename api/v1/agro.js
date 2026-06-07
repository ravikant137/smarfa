// /api/v1/agro.js - Proxy for Agromonitoring API to fix CORS issues
const AGRO_API_KEY = process.env.AGRO_API_KEY || '8518d290ab4e6f4ca86ee6c7d841b3fb';
const AGRO_BASE = 'https://api.agromonitoring.com/agro/1.0';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();

  const { action } = req.query;

  try {
    if (action === 'register-polygon') {
      // POST polygon to Agromonitoring
      const agroRes = await fetch(`${AGRO_BASE}/polygons?appid=${AGRO_API_KEY}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req.body)
      });
      const data = await agroRes.json();
      return res.status(agroRes.status).json(data);
    }

    if (action === 'image-search') {
      const { start, end, polyid } = req.query;
      const agroRes = await fetch(`${AGRO_BASE}/image/search?start=${start}&end=${end}&polyid=${polyid}&appid=${AGRO_API_KEY}`);
      const data = await agroRes.json();
      return res.status(agroRes.status).json(data);
    }

    if (action === 'ndvi-history') {
      const { polyid } = req.query;
      const agroRes = await fetch(`${AGRO_BASE}/ndvi/history?polyid=${polyid}&appid=${AGRO_API_KEY}`);
      const data = await agroRes.json();
      return res.status(agroRes.status).json(data);
    }

    if (action === 'weather') {
      // Current weather for a point
      const { lat, lon } = req.query;
      const agroRes = await fetch(`${AGRO_BASE}/weather?lat=${lat}&lon=${lon}&appid=${AGRO_API_KEY}&units=metric`);
      const data = await agroRes.json();
      return res.status(agroRes.status).json(data);
    }

    if (action === 'soil') {
      // Soil data (moisture, temperature at multiple depths)
      const { polyid } = req.query;
      const agroRes = await fetch(`${AGRO_BASE}/soil?polyid=${polyid}&appid=${AGRO_API_KEY}`);
      const data = await agroRes.json();
      return res.status(agroRes.status).json(data);
    }

    if (action === 'weather-forecast') {
      // 7-day weather forecast for a polygon
      const { polyid } = req.query;
      const agroRes = await fetch(`${AGRO_BASE}/weather/forecast?polyid=${polyid}&appid=${AGRO_API_KEY}&units=metric&cnt=7`);
      const data = await agroRes.json();
      return res.status(agroRes.status).json(data);
    }

    if (action === 'precipitation') {
      // Historical accumulated precipitation
      const { polyid } = req.query;
      const end = Math.floor(Date.now() / 1000);
      const start = end - (7 * 24 * 60 * 60); // last 7 days
      const agroRes = await fetch(`${AGRO_BASE}/weather/history?polyid=${polyid}&start=${start}&end=${end}&appid=${AGRO_API_KEY}&units=metric`);
      const data = await agroRes.json();
      return res.status(agroRes.status).json(data);
    }

    return res.status(400).json({ error: 'Unknown action' });

  } catch (err) {
    console.error('Agro proxy error:', err);
    return res.status(500).json({ error: err.message });
  }
}
