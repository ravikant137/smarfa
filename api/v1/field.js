// api/v1/field.js — Field registration, area calculation, crop management

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();

  const { action } = req.query;

  if (action === 'calculate-area') {
    // Calculate polygon area in acres from GPS coordinates using the Shoelace formula
    const { coordinates } = req.body; // array of [lat, lon]
    if (!coordinates || coordinates.length < 3) {
      return res.status(400).json({ error: 'At least 3 coordinates required' });
    }

    // Convert lat/lon to meters using equirectangular approximation
    const toRadians = deg => deg * Math.PI / 180;
    const R = 6371000; // Earth radius in meters
    const origin = coordinates[0];
    const points = coordinates.map(([lat, lon]) => ({
      x: R * toRadians(lon - origin[1]) * Math.cos(toRadians(origin[0])),
      y: R * toRadians(lat - origin[0])
    }));

    // Shoelace formula for polygon area in square meters
    let area = 0;
    for (let i = 0; i < points.length; i++) {
      const j = (i + 1) % points.length;
      area += points[i].x * points[j].y;
      area -= points[j].x * points[i].y;
    }
    const areaSqMeters = Math.abs(area / 2);
    const areaAcres = areaSqMeters / 4046.86;
    const areaHectares = areaSqMeters / 10000;

    return res.status(200).json({
      sqMeters: Math.round(areaSqMeters),
      acres: parseFloat(areaAcres.toFixed(2)),
      hectares: parseFloat(areaHectares.toFixed(3))
    });
  }

  return res.status(400).json({ error: 'Unknown action. Use: calculate-area' });
}
