// api/v1/weather.js — Open-Meteo weather proxy + AI Agronomy impact calculation

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  if (req.method === 'OPTIONS') return res.status(200).end();

  const { lat, lon } = req.query;
  if (!lat || !lon) return res.status(400).json({ error: 'lat and lon required' });

  try {
    const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}` +
      `&current=temperature_2m,relative_humidity_2m` +
      `&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum` +
      `&timezone=auto&past_days=3`;

    const weatherRes = await fetch(url);
    const data = await weatherRes.json();

    if (!data || !data.daily) return res.status(502).json({ error: 'Weather API failed' });

    // Calculate AI Agronomy Impact on the server
    let pastRainVolume = 0;
    let futureRainVolume = 0;
    let max3DaysTemp = -99;
    let min3DaysTemp = 99;
    let max3DaysRain = 0;

    for (let i = 0; i < 3; i++) {
      if (data.daily.precipitation_sum[i]) pastRainVolume += data.daily.precipitation_sum[i];
    }
    for (let i = 3; i < Math.min(6, data.daily.time.length); i++) {
      if (data.daily.temperature_2m_max[i] > max3DaysTemp) max3DaysTemp = data.daily.temperature_2m_max[i];
      if (data.daily.temperature_2m_min[i] < min3DaysTemp) min3DaysTemp = data.daily.temperature_2m_min[i];
      if (data.daily.precipitation_probability_max[i] > max3DaysRain) max3DaysRain = data.daily.precipitation_probability_max[i];
      if (data.daily.precipitation_sum[i]) futureRainVolume += data.daily.precipitation_sum[i];
    }

    const impacts = [];
    let topImpact = { text: 'Optimal', color: 'green', icon: '✅' };

    if (pastRainVolume > 30 && futureRainVolume > 10) {
      impacts.push({ type: 'critical', title: '🚨 Critical Waterlogging Risk', body: `Fields received ${pastRainVolume.toFixed(1)}mm rain in past 3 days. Soil is saturated. Additional ${futureRainVolume.toFixed(1)}mm expected. Do NOT irrigate!` });
      topImpact = { text: 'Waterlogging', color: 'red', icon: '🚨' };
    } else if (pastRainVolume > 20) {
      impacts.push({ type: 'good', title: '💧 Historical Saturation', body: `Received ${pastRainVolume.toFixed(1)}mm recently. Skip current irrigation cycles.` });
      topImpact = { text: 'High Moisture', color: 'blue', icon: '💧' };
    } else if (pastRainVolume < 5 && futureRainVolume < 5) {
      impacts.push({ type: 'warning', title: '🌵 Dry Soil Profile', body: `Only ${pastRainVolume.toFixed(1)}mm in past 3 days. Deep irrigation highly recommended.` });
      topImpact = { text: 'Dry Soil', color: 'yellow', icon: '🌵' };
    }

    if (futureRainVolume > 40) {
      impacts.push({ type: 'critical', title: `🌊 Heavy Downpour Alert (~${futureRainVolume.toFixed(1)}mm)`, body: 'High risk of waterlogging and root rot. Clear drainage channels.' });
      topImpact = { text: 'Heavy Rain', color: 'red', icon: '🌊' };
    } else if (max3DaysRain > 50) {
      impacts.push({ type: 'critical', title: `🌧️ High Rain Risk (${Math.round(max3DaysRain)}%)`, body: 'Delay pesticide/fertilizer sprays. Risk of fungal diseases (Blight, Mildew).' });
      if (topImpact.text === 'Optimal') topImpact = { text: 'Fungal Risk', color: 'red', icon: '🌧️' };
    } else if (futureRainVolume >= 10 && futureRainVolume <= 40 && pastRainVolume <= 20) {
      impacts.push({ type: 'good', title: `💧 Expected Moisture Recharge (~${futureRainVolume.toFixed(1)}mm)`, body: 'Soil will be hydrated. Skip next 1-2 irrigation cycles.' });
    } else if (max3DaysRain > 20) {
      impacts.push({ type: 'warning', title: '🌦️ Light Rain Possible', body: 'Monitor soil moisture. Minor pest activity may increase.' });
    }

    if (max3DaysTemp > 35) {
      impacts.push({ type: 'critical', title: `🌡️ Heat Stress Alert (${Math.round(max3DaysTemp)}°C)`, body: 'Risk of flower drop in Tomatoes/Cotton. Increase irrigation frequency.' });
      topImpact = { text: 'Heat Stress', color: 'red', icon: '🌡️' };
    }
    if (min3DaysTemp < 10) {
      impacts.push({ type: 'info', title: `❄️ Cold Snap Alert (${Math.round(min3DaysTemp)}°C)`, body: 'Risk of frost damage to seedlings. Consider light evening irrigation.' });
      topImpact = { text: 'Frost Risk', color: 'blue', icon: '❄️' };
    }
    if (impacts.length === 0) {
      impacts.push({ type: 'good', title: '✅ Optimal Conditions', body: 'Weather is stable. Excellent window for fertilizer application and standard irrigation.' });
    }

    return res.status(200).json({
      weather: data,
      agronomyImpact: { impacts, topImpact, pastRainVolume, futureRainVolume, max3DaysTemp, min3DaysTemp, max3DaysRain }
    });

  } catch (err) {
    console.error('Weather proxy error:', err);
    return res.status(500).json({ error: err.message });
  }
}
