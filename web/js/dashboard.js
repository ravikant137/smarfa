// web/js/dashboard.js — Map init, stat cards, market prices, field data

(function() {

  let dashMap = null;
  let _mapInited = false;

  window.dashMap = null;

  // ── Market Prices ──────────────────────────────────────────────
  window.fetchMarketPrices = function() {
    const API = window.APP ? window.APP.API : window.location.origin;
    fetch(`${API}/api/v1/market`)
      .then(r => r.json())
      .then(data => {
        if (!data || !data.prices) return;
        const ticker = document.getElementById('market-ticker');
        if (!ticker) return;
        ticker.innerHTML = data.prices.map(p => {
          const arrow = p.trend === 'up' ? '▲' : p.trend === 'down' ? '▼' : '—';
          const color = p.trend === 'up' ? 'var(--green)' : p.trend === 'down' ? 'var(--red)' : 'var(--muted)';
          return `<span style="font-size:13px;color:var(--text);font-weight:600;white-space:nowrap;">
            ${p.crop}: <b>${p.unit.split('/')[0]}${p.price.toLocaleString()}</b>
            <span style="color:${color};font-size:11px;">${arrow}${Math.abs(p.change)}</span>
          </span>`;
        }).join('<span style="color:var(--border);margin:0 8px;">|</span>');
      })
      .catch(() => {});
  };

  // ── Dashboard Map ──────────────────────────────────────────────
  window.initDashboardMap = function() {
    if (_mapInited) return;
    _mapInited = true;

    const API = window.APP ? window.APP.API : window.location.origin;

    function loadMapAtLocation(lat, lon) {
      window.APP.userLat = lat;
      window.APP.userLon = lon;

      const overlay = document.getElementById('map-loading-overlay');
      if (overlay) overlay.style.display = 'none';

      if (window.dashMap) { window.dashMap.remove(); window.dashMap = null; }
      window.dashMap = L.map('farm-map').setView([lat, lon], 16);

      L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
        maxZoom: 20, attribution: '© Google Earth Engine'
      }).addTo(window.dashMap);

      // Initialize polygon drawing tool
      if (window.initSatelliteDrawing) window.initSatelliteDrawing(window.dashMap);

      // Radius ring
      L.circle([lat, lon], {
        color: '#f59e0b', fillColor: '#f59e0b', fillOpacity: 0.1,
        radius: 2000, weight: 1, dashArray: '5, 10'
      }).addTo(window.dashMap);

      // GPS marker
      const icon = L.divIcon({
        className: 'pulse-icon',
        html: '<div style="width:16px;height:16px;background:var(--green);border-radius:50%;box-shadow:0 0 20px 4px var(--green);animation:pulse 2s infinite;"></div>',
        iconSize: [16, 16]
      });
      L.marker([lat, lon], { icon }).addTo(window.dashMap);

      // Update location subtitle
      const locEl = document.getElementById('map-location-sub');
      fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json`)
        .then(r => r.json())
        .then(geo => {
          if (locEl && geo.address) {
            const city = geo.address.city || geo.address.town || geo.address.village || '';
            const state = geo.address.state || '';
            locEl.innerHTML = `📍 Live GPS: ${city}${city && state ? ', ' : ''}${state}`;
          }
        }).catch(() => {});

      // Fetch weather for this location
      if (window.fetchWeatherData) window.fetchWeatherData(lat, lon);

      // Fetch additional Open-Meteo data for temp stat card
      fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true&daily=temperature_2m_max,temperature_2m_min&timezone=auto`)
        .then(r => r.json())
        .then(wData => {
          if (wData && wData.current_weather) {
            const tempEl = document.getElementById('s-temp');
            if (tempEl && tempEl.textContent === '—') {
              tempEl.textContent = Math.round(wData.current_weather.temperature) + '°C';
              const sub = document.getElementById('s-temp-sub');
              if (sub && wData.daily) sub.textContent = Math.round(wData.daily.temperature_2m_min[0]) + '° – ' + Math.round(wData.daily.temperature_2m_max[0]) + '°';
            }
          }
        }).catch(() => {});
    }

    function fallbackToIP() {
      fetch('https://ipapi.co/json/')
        .then(r => r.json())
        .then(d => loadMapAtLocation(d.latitude || 15.3647, d.longitude || 75.1240))
        .catch(() => loadMapAtLocation(15.3647, 75.1240));
    }

    if (!navigator.geolocation) { fallbackToIP(); return; }

    const timeout = setTimeout(() => { console.warn('GPS timeout, using IP'); fallbackToIP(); }, 4000);
    navigator.geolocation.getCurrentPosition(
      pos => { clearTimeout(timeout); loadMapAtLocation(pos.coords.latitude, pos.coords.longitude); },
      () => { clearTimeout(timeout); fallbackToIP(); },
      { enableHighAccuracy: true, timeout: 3500, maximumAge: 0 }
    );
  };

})();
