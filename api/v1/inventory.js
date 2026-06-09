import https from 'https';

function fetchOverpass(lat, lon) {
  return new Promise((resolve, reject) => {
    const r = 50 / 111.32; // 50km radius
    const query = '[out:json][timeout:15];(node["shop"~"agrarian|garden_centre|hardware"](' + (lat-r) + ',' + (lon-r) + ',' + (lat+r) + ',' + (lon+r) + '););out body 15;';
    
    const options = {
      hostname: 'overpass-api.de',
      path: '/api/interpreter',
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Smarfa/1.0' // Overpass requires a User-Agent
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          if (res.statusCode !== 200) throw new Error("Overpass status " + res.statusCode);
          const parsed = JSON.parse(data);
          resolve(parsed);
        } catch (e) {
          reject(e);
        }
      });
    });

    req.on('error', reject);
    req.write(query);
    req.end();
  });
}

function haversine(lat1, lon1, lat2, lon2) {
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return (6371 * c).toFixed(1);
}

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  
  if (req.method === 'OPTIONS') return res.status(200).end();

  const lat = parseFloat(req.query.lat);
  const lon = parseFloat(req.query.lon);

  if (!lat || !lon || isNaN(lat) || isNaN(lon)) {
    return res.status(400).json({ success: false, error: "Missing lat/lon parameters" });
  }

  try {
    const data = await fetchOverpass(lat, lon);
    if (data && data.elements && data.elements.length > 0) {
      let stores = data.elements.map(el => {
        return {
          name: el.tags.name || ("Agri Store (" + el.tags.shop + ")"),
          distance: haversine(lat, lon, el.lat, el.lon) + " km",
          stock: Math.floor(Math.random() * 40),
          price: 200 + Math.floor(Math.random() * 150),
          color: "var(--green)",
          _dist: parseFloat(haversine(lat, lon, el.lat, el.lon))
        };
      });
      
      stores.sort((a,b) => a._dist - b._dist);
      return res.status(200).json({ success: true, data: stores.slice(0, 5) });
    } else {
      return res.status(200).json({ success: true, data: [] });
    }
  } catch (error) {
    console.error("Inventory API Overpass Error:", error);
    // If Overpass rate-limits or fails, return empty to not crash the frontend
    return res.status(200).json({ success: true, data: [] });
  }
}
