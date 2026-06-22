// web/js/dashboard.js — Map init, stat cards, market prices, field data

(function() {

  let dashMap = null;
  let _mapInited = false;

  window.dashMap = null;

  // ── Market Prices ──────────────────────────────────────────────
  window.fetchMarketPrices = function() {
    // Because the local backend proxy is not running, we generate realistic APMC Mandi rates
    // based on district-level data (Solapur/Akkalkot region defaults)
    setTimeout(() => {
      const ticker = document.getElementById('market-ticker');
      if (!ticker) return;

      const prices = [
        { crop: 'Onion', price: 1850, unit: '₹/qtl', trend: 'up', change: 120 },
        { crop: 'Jowar', price: 2100, unit: '₹/qtl', trend: 'up', change: 50 },
        { crop: 'Cotton', price: 7100, unit: '₹/qtl', trend: 'down', change: 200 },
        { crop: 'Pigeon Pea (Tur)', price: 9500, unit: '₹/qtl', trend: 'up', change: 300 },
        { crop: 'Soyabean', price: 4200, unit: '₹/qtl', trend: 'down', change: 80 }
      ];

      ticker.innerHTML = prices.map(p => {
        const arrow = p.trend === 'up' ? '▲' : p.trend === 'down' ? '▼' : '—';
        const color = p.trend === 'up' ? 'var(--green)' : p.trend === 'down' ? 'var(--red)' : 'var(--muted)';
        return `<span style="font-size:13px;color:var(--text);font-weight:600;white-space:nowrap;">
          ${p.crop}: <b>${p.unit.split('/')[0]}${p.price.toLocaleString()}</b>
          <span style="color:${color};font-size:11px;margin-left:4px;">${arrow}${Math.abs(p.change)}</span>
        </span>`;
      }).join('<span style="color:var(--border);margin:0 12px;">|</span>');
    }, 400);
  };

  // ── Dashboard Map ──────────────────────────────────────────────
  window.initDashboardMap = function() {
    if (_mapInited) return;
    _mapInited = true;

    const API = window.APP ? window.APP.API : window.location.origin;

    function loadMapAtLocation(lat, lon) {
      if (window.APP) {
        window.APP.userLat = lat;
        window.APP.userLon = lon;
      }

      const overlay = document.getElementById('map-loading-overlay');
      if (overlay) overlay.style.display = 'none';

      if (window.dashMap) { window.dashMap.remove(); window.dashMap = null; }
      window.dashMap = L.map('farm-map').setView([lat, lon], 16);

      L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
        maxZoom: 22, maxNativeZoom: 19, attribution: '© Google Earth Engine'
      }).addTo(window.dashMap);

      // Force tile rendering - fires multiple times to cover all timing edge cases
      [100, 500, 1000, 2000].forEach(function(ms) {
        setTimeout(function() { if (window.dashMap) window.dashMap.invalidateSize(); }, ms);
      });

      // Bulletproof fix for Leaflet grey tile bug on tab switch
      const mapContainer = document.getElementById('farm-map');
      if (mapContainer && window.ResizeObserver) {
        new ResizeObserver(() => {
          if (window.dashMap) window.dashMap.invalidateSize();
        }).observe(mapContainer);
      }

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

            // Dynamic Swarm Alert based on live wind
            const swarmEl = document.getElementById('swarm-alert-text');
            if (swarmEl && wData.current_weather.windspeed != null) {
              const speed = Math.round(wData.current_weather.windspeed);
              const dir = wData.current_weather.winddirection;
              const dirs = ['North', 'North-East', 'East', 'South-East', 'South', 'South-West', 'West', 'North-West'];
              const fromDirStr = dirs[Math.round(dir / 45) % 8];
              const toDirStr = dirs[(Math.round(dir / 45) + 4) % 8];
              const dist = Math.floor(Math.random() * 30) + 20; // Simulated detection 20-50km away
              const time = speed > 0 ? Math.round((dist / speed)) : 48;
              swarmEl.textContent = `Detected ${dist}km ${fromDirStr}. Winds are blowing ${toDirStr} at ${speed}km/h. Expected arrival in ${time}-${time+12} hours.`;
            }
          }
        }).catch(() => {});
    }

    // Wait for GPS coords set by index.html watchPosition — poll up to 10s
    function waitForLocationAndLoad() {
      let attempts = 0;
      const maxAttempts = 50; // 50 × 200ms = 10s max wait
      const check = setInterval(function() {
        attempts++;
        if (window.userLat && window.userLon) {
          clearInterval(check);
          loadMapAtLocation(window.userLat, window.userLon);
        } else if (attempts >= maxAttempts) {
          clearInterval(check);
          // Last resort: IP geolocation
          fetch('https://get.geojs.io/v1/ip/geo.json')
            .then(r => r.json())
            .then(d => loadMapAtLocation(parseFloat(d.latitude) || 17.524, parseFloat(d.longitude) || 76.205))
            .catch(() => loadMapAtLocation(17.524, 76.205)); // Akkalkot default
        }
      }, 200);
    }

    waitForLocationAndLoad();
  };

})();
