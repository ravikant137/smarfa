// web/js/weather.js — Weather fetching and rendering

(function() {

  function getWeatherIcon(code) {
    if (code <= 1) return '☀️';
    if (code <= 3) return '⛅';
    if (code <= 48) return '🌫️';
    if (code <= 67) return '🌧️';
    if (code <= 77) return '❄️';
    if (code <= 82) return '🌦️';
    if (code >= 95) return '⛈️';
    return '☁️';
  }

  function renderImpactCard(impact) {
    const colors = { critical: 'var(--red)', good: 'var(--green)', warning: 'var(--yellow)', info: '#2c9adb' };
    const color = colors[impact.type] || 'var(--muted)';
    return `<div style="background:${color}11; border-left:3px solid ${color}; padding:10px 14px; border-radius:4px; font-size:14px; color:var(--text); line-height:1.4; margin-bottom:8px;">
      <strong>${impact.title}:</strong> ${impact.body}
    </div>`;
  }

  window.fetchWeatherData = function(lat, lon) {
    const API = window.APP ? window.APP.API : window.location.origin;

    // 1. Agromonitoring live field weather (precision data for stat cards)
    fetch(`${API}/api/v1/agro?action=weather&lat=${lat}&lon=${lon}`)
      .then(r => r.json())
      .then(w => {
        if (!w || !w.main) return;
        const temp = Math.round(w.main.temp);
        const humidity = w.main.humidity;
        const feelsLike = Math.round(w.main.feels_like);
        const windSpeed = w.wind ? (w.wind.speed * 3.6).toFixed(1) : null;
        const cloudCover = w.clouds ? w.clouds.all : null;
        const description = w.weather && w.weather[0] ? w.weather[0].description : '';

        const tempEl = document.getElementById('s-temp');
        const tempSub = document.getElementById('s-temp-sub');
        const moistEl = document.getElementById('s-moisture');
        const moistSub = document.getElementById('s-moisture-sub');

        if (tempEl) tempEl.textContent = temp + '°C';
        if (tempSub) tempSub.textContent = `Feels ${feelsLike}°C · ${description}`;
        if (moistEl) moistEl.textContent = humidity + '%';
        if (moistSub) moistSub.textContent = (windSpeed ? `💨 ${windSpeed} km/h` : 'Humidity') + (cloudCover !== null ? ` · ☁️ ${cloudCover}%` : '');
      })
      .catch(() => {}); // falls back to Open-Meteo below

    // 2. Open-Meteo forecast + AI Agronomy Impact (backend-calculated)
    fetch(`${API}/api/v1/weather?lat=${lat}&lon=${lon}`)
      .then(r => r.json())
      .then(result => {
        if (!result || !result.weather || !result.weather.daily) return;

        const data = result.weather;
        const agronomy = result.agronomyImpact;
        const daysDiv = document.getElementById('weather-days');
        const container = document.getElementById('weather-forecast-container');
        if (!container || !daysDiv) return;

        container.style.display = 'block';
        daysDiv.innerHTML = '';
        const daysOfWeek = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        let rainAlert = false;
        const rainDays = [];

        // Today is index 3 (past_days=3)
        for (let i = 3; i < Math.min(10, data.daily.time.length); i++) {
          const dateObj = new Date(data.daily.time[i]);
          const dayName = i === 3 ? 'Today' : i === 4 ? 'Tmrw' : daysOfWeek[dateObj.getDay()];
          const maxT = Math.round(data.daily.temperature_2m_max[i]);
          const minT = Math.round(data.daily.temperature_2m_min[i]);
          const rainProb = data.daily.precipitation_probability_max[i];
          const icon = getWeatherIcon(data.daily.weather_code[i]);

          if (i > 3 && i <= 6 && rainProb > 50) { rainAlert = true; rainDays.push(dayName); }

          daysDiv.innerHTML += `<div style="flex:1;background:var(--bg);border-radius:12px;padding:14px 10px;min-width:80px;text-align:center;border:1px solid var(--border);">
            <div style="font-size:12px;font-weight:700;margin-bottom:8px;color:var(--muted);">${dayName}</div>
            <div style="font-size:28px;margin-bottom:8px;">${icon}</div>
            <div style="font-size:15px;font-weight:800;color:var(--text);">${maxT}°</div>
            <div style="font-size:12px;color:var(--muted);margin-bottom:6px;">${minT}°</div>
            <div style="font-size:11px;font-weight:700;color:var(--sky);background:rgba(91,164,207,0.1);padding:3px 0;border-radius:6px;">💧 ${rainProb}%</div>
          </div>`;
        }

        // Render agronomy impacts (computed server-side)
        const impactContainer = document.getElementById('weather-impact-container');
        const impactList = document.getElementById('weather-impact-list');
        if (impactList && agronomy) {
          impactList.innerHTML = agronomy.impacts.map(renderImpactCard).join('');
          impactContainer.style.display = 'block';

          // Update Crop Impact stat card
          const topImpact = agronomy.topImpact;
          const impactCard = document.getElementById('s-impact');
          const impactIcon = document.getElementById('s-impact-icon');
          const colorMap = { red: 'var(--red)', green: 'var(--green)', blue: 'var(--sky)', yellow: 'var(--yellow)' };
          if (impactCard) {
            impactCard.textContent = topImpact.text;
            impactCard.style.color = colorMap[topImpact.color] || 'var(--text)';
          }
          if (impactIcon) impactIcon.textContent = topImpact.icon;
        }

        // Fallback: update stat cards from Open-Meteo if Agro weather hasn't responded
        if (data.current) {
          const tempEl = document.getElementById('s-temp');
          if (tempEl && tempEl.textContent === '—') {
            tempEl.textContent = Math.round(data.current.temperature_2m) + '°C';
            document.getElementById('s-temp-sub').textContent = 'Current Temp';
          }
          const moistEl = document.getElementById('s-moisture');
          if (moistEl && moistEl.textContent === '—') {
            moistEl.textContent = data.current.relative_humidity_2m + '%';
            document.getElementById('s-moisture-sub').textContent = 'Humidity';
          }
        }

        // Rain notification
        if (rainAlert) {
          setTimeout(() => window.toast(`🌦️ Rain expected on ${rainDays.join(' & ')}. Plan irrigation accordingly!`, 'warning'), 2000);
        }
      })
      .catch(err => console.warn('Weather fetch failed:', err));
  };

})();
