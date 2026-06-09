// web/js/satellite.js — Polygon drawing, NDVI rendering, soil + rain overlays

(function() {

  window.initSatelliteDrawing = function(map) {
    const API = window.APP ? window.APP.API : window.location.origin;
    const drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);
    window.drawnItems = drawnItems;

    const drawControl = new L.Control.Draw({
      draw: {
        polyline: false,
        polygon: {
          allowIntersection: false,
          shapeOptions: { color: '#3d7a3a', weight: 3, fillColor: '#3d7a3a', fillOpacity: 0.2 }
        },
        circle: false, rectangle: false, circlemarker: false, marker: false
      },
      edit: { featureGroup: drawnItems, remove: true }
    });
    map.addControl(drawControl);

    window.currentPolygonCoordinates = null;
    map.on(L.Draw.Event.CREATED, function(e) {
      if (e.layerType === 'polygon') {
        drawnItems.clearLayers();
        drawnItems.addLayer(e.layer);
        const latlngs = e.layer.getLatLngs()[0];
        window.currentPolygonCoordinates = latlngs.map(ll => [ll.lat, ll.lng]);

        // Calculate real area from backend
        fetch(`${API}/api/v1/field?action=calculate-area`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ coordinates: window.currentPolygonCoordinates })
        }).then(r => r.json()).then(areaData => {
          if (areaData.acres) {
            const areaEl = document.getElementById('field-detail-area');
            if (areaEl) areaEl.textContent = areaData.acres + ' acres (' + areaData.hectares + ' ha)';
          }
        }).catch(() => {});

        const btn = document.getElementById('analyze-field-btn');
        if (btn) btn.style.display = 'block';
        window.toast('Farm boundary drawn! Click "🛰️ Analyze Field" for satellite scan.');
      }
    });
  };

  window.analyzeDrawnField = function() {
    const map = window.dashMap;
    if (!window.currentPolygonCoordinates || !map) return;

    const API = window.APP ? window.APP.API : window.location.origin;
    const btn = document.getElementById('analyze-field-btn');
    btn.innerHTML = '🔄 Processing...';
    btn.style.pointerEvents = 'none';

    const geoJsonCoords = window.currentPolygonCoordinates.map(ll => [ll[1], ll[0]]);
    geoJsonCoords.push(geoJsonCoords[0]);

    const polygonData = {
      name: 'Smarfa Field ' + Date.now(),
      geo_json: {
        type: 'Feature', properties: {},
        geometry: { type: 'Polygon', coordinates: [geoJsonCoords] }
      }
    };

    fetch(`${API}/api/v1/agro?action=register-polygon`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(polygonData)
    })
    .then(r => r.json())
    .then(polyResponse => {
      if (!polyResponse || !polyResponse.id) throw new Error('Polygon registration failed: ' + JSON.stringify(polyResponse));
      const polyId = polyResponse.id;

      window.drawnItems.clearLayers();
      const outline = L.polygon(window.currentPolygonCoordinates, {
        color: '#00e5ff', weight: 3, fillColor: '#00e5ff', fillOpacity: 0.1
      }).addTo(map);
      map.fitBounds(outline.getBounds());

      const endUnix = Math.floor(Date.now() / 1000);
      const startUnix = endUnix - (90 * 24 * 60 * 60);

      return Promise.all([
        fetch(`${API}/api/v1/agro?action=image-search&polyid=${polyId}&start=${startUnix}&end=${endUnix}`).then(r => r.json()).catch(() => []),
        fetch(`${API}/api/v1/agro?action=ndvi-history&polyid=${polyId}`).then(r => r.json()).catch(() => []),
        fetch(`${API}/api/v1/agro?action=soil&polyid=${polyId}`).then(r => r.json()).catch(() => null),
        fetch(`${API}/api/v1/agro?action=precipitation&polyid=${polyId}`).then(r => r.json()).catch(() => [])
      ]).then(([images, ndviHistory, soil, precip]) => {
        renderNDVI(map, outline, ndviHistory);
        renderSoilData(soil);
        renderRainOverlay(map, precip);
        updateFieldDetailPanel(images, ndviHistory, soil, precip);
        btn.innerHTML = '✅ Analysis Done';
        btn.style.background = 'var(--sky)';
      });
    })
    .catch(err => {
      console.error('Satellite Error:', err);
      window.toast('Satellite analysis failed: ' + err.message, 'error');
      btn.innerHTML = '🛰️ Analyze Field';
      btn.style.pointerEvents = 'auto';
    });
  };

  function ndviToColor(v) {
    if (v == null) return '#94a3b8';
    if (v < 0.1) return '#ef4444';
    if (v < 0.2) return '#f97316';
    if (v < 0.35) return '#f59e0b';
    if (v < 0.5) return '#84cc16';
    return '#16a34a';
  }

  function ndviLabel(mean) {
    if (mean == null) return 'No Data';
    if (mean < 0.1) return 'Bare Soil / Severe Stress';
    if (mean < 0.2) return 'Severe Stress';
    if (mean < 0.35) return 'Moderate Stress';
    if (mean < 0.5) return 'Moderate Health';
    return 'Healthy Crop';
  }

  function renderNDVI(map, outline, ndviHistory) {
    var ndviStats = null;
    if (ndviHistory && ndviHistory.length > 0) {
      ndviHistory.sort((a, b) => b.dt - a.dt);
      ndviStats = ndviHistory[0].data;
    }
    const mean = ndviStats ? ndviStats.mean : null;
    const min = ndviStats ? ndviStats.min : null;
    const max = ndviStats ? ndviStats.max : null;
    const color = ndviToColor(mean);

    outline.setStyle({ fillColor: color, fillOpacity: 0.55, color: '#fff', weight: 2 });

    if (ndviStats && max - min > 0.1) {
      const b = outline.getBounds();
      L.polygon([
        [b.getNorth(), b.getWest()], [b.getNorth(), (b.getWest() + b.getEast()) / 2],
        [(b.getNorth() + b.getSouth()) / 2, (b.getWest() + b.getEast()) / 2],
        [(b.getNorth() + b.getSouth()) / 2, b.getWest()]
      ], { color: 'transparent', weight: 0, fillColor: ndviToColor(min), fillOpacity: 0.45 }).addTo(map);
    }

    window._ndviMean = mean;
    window._ndviColor = color;
    window._ndviLabel = ndviLabel(mean);
  }

  function renderSoilData(soil) {
    const soilMoisture = (soil && soil.moisture != null) ? (soil.moisture * 100).toFixed(1) : null;
    const soilTemp = (soil && soil.t0 != null) ? (soil.t0 - 273.15).toFixed(1) : null;
    window._soilMoisture = soilMoisture;

    if (soilMoisture) {
      const el = document.getElementById('s-moisture');
      const sub = document.getElementById('s-moisture-sub');
      if (el) el.textContent = soilMoisture + '%';
      if (sub) sub.textContent = '🌍 Satellite Soil' + (soilTemp ? ' · ' + soilTemp + '°C' : '');

      const plantedEl = document.getElementById('field-detail-planted');
      if (plantedEl) plantedEl.textContent = soilMoisture + '%' + (soilTemp ? ' · ' + soilTemp + '°C' : '');
    }
  }

  function renderRainOverlay(map, precip) {
    let totalRain7d = 0;
    if (Array.isArray(precip)) precip.forEach(d => { totalRain7d += d.rain ? (d.rain['3h'] || d.rain['1h'] || 0) : 0; });
    window._rain7d = totalRain7d;
    const rainColor = totalRain7d > 40 ? '#ef4444' : totalRain7d > 15 ? '#f59e0b' : '#3b82f6';

    if (window.APP && window.APP.userLat) {
      L.circle([window.APP.userLat, window.APP.userLon], {
        color: rainColor, fillColor: rainColor, fillOpacity: 0.08, radius: 900, weight: 2, dashArray: '5 8'
      })
      .bindPopup(`<b>💧 Rain (7d): ${totalRain7d.toFixed(1)}mm</b><br>${totalRain7d > 40 ? '🚨 Heavy—check drainage' : totalRain7d > 15 ? '🌧️ Moderate—skip irrigation' : '☀️ Dry—irrigate as needed'}`)
      .addTo(map);
    }
  }

  function updateFieldDetailPanel(images, ndviHistory, soil, precip) {
    const mean = window._ndviMean;
    const color = window._ndviColor;
    const label = window._ndviLabel;
    const soilMoisture = window._soilMoisture;
    const totalRain = window._rain7d;
    const rainColor = (totalRain || 0) > 40 ? '#ef4444' : (totalRain || 0) > 15 ? '#f59e0b' : '#3b82f6';

    const imgDate = (images && images.length) ? new Date(images.sort((a, b) => b.dt - a.dt)[0].dt * 1000).toLocaleDateString() : 'Latest';

    let variabilityHTML = '';
    if (ndviHistory && ndviHistory.length > 0 && ndviHistory[0].data) {
      const stats = ndviHistory[0].data;
      const spread = stats.max - stats.min;
      if (spread > 0.1) {
        variabilityHTML = `<hr style="border:none;border-top:1px solid #eee;margin:6px 0;">
          <div style="font-size:11px;color:#666;font-weight:700;margin-bottom:4px;">🎯 MANAGEMENT ZONES</div>
          <div style="font-size:10px;display:flex;justify-content:space-between;margin-bottom:2px;"><span>High Yield Potential:</span><b style="color:#16a34a">Top 30%</b></div>
          <div style="font-size:10px;display:flex;justify-content:space-between;"><span>Needs N-Fertilizer:</span><b style="color:#ef4444">Bottom 20%</b></div>`;
      } else {
        variabilityHTML = `<hr style="border:none;border-top:1px solid #eee;margin:6px 0;">
          <div style="font-size:11px;color:#666;font-weight:700;margin-bottom:4px;">🎯 MANAGEMENT ZONES</div>
          <div style="font-size:10px;color:var(--muted);">Field is uniform. Standard application.</div>`;
      }
    }

    // Map legend
    if (window._agroLegend && window.dashMap) window.dashMap.removeControl(window._agroLegend);
    const legend = L.control({ position: 'bottomleft' });
    legend.onAdd = function() {
      const d = L.DomUtil.create('div');
      d.style.cssText = 'background:#fff;padding:12px 14px;border-radius:12px;font-size:12px;font-weight:700;box-shadow:0 4px 16px rgba(0,0,0,0.15);';
      d.innerHTML = `<div style="font-size:11px;color:#666;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">🛰️ Satellite Analysis</div>
        <div style="display:flex;align-items:center;gap:5px;margin-bottom:3px;"><span style="width:12px;height:12px;background:#16a34a;border-radius:2px;display:inline-block;"></span> Healthy NDVI &gt;0.5</div>
        <div style="display:flex;align-items:center;gap:5px;margin-bottom:3px;"><span style="width:12px;height:12px;background:#84cc16;border-radius:2px;display:inline-block;"></span> Moderate 0.35–0.5</div>
        <div style="display:flex;align-items:center;gap:5px;margin-bottom:3px;"><span style="width:12px;height:12px;background:#f59e0b;border-radius:2px;display:inline-block;"></span> Stressed 0.2–0.35</div>
        <div style="display:flex;align-items:center;gap:5px;margin-bottom:6px;"><span style="width:12px;height:12px;background:#ef4444;border-radius:2px;display:inline-block;"></span> Severe &lt;0.2</div>
        <hr style="border:none;border-top:1px solid #eee;margin:4px 0;">
        ${mean != null ? `<div style="color:#333;">📊 NDVI: <b style="color:${color}">${mean.toFixed(3)}</b> — ${label}</div>` : ''}
        ${soilMoisture ? `<div style="color:#3b82f6;margin-top:3px;">🌍 Soil: <b>${soilMoisture}%</b></div>` : ''}
        ${totalRain != null ? `<div style="color:${rainColor};margin-top:3px;">💧 Rain 7d: <b>${totalRain.toFixed(1)}mm</b></div>` : ''}
        ${variabilityHTML}`;
      return d;
    };
    if (window.dashMap) legend.addTo(window.dashMap);
    window._agroLegend = legend;

    // Field detail status panel
    const detailEl = document.getElementById('field-detail');
    if (detailEl) {
      detailEl.style.display = 'block';
      const nameEl = document.getElementById('field-detail-name');
      const statusEl = document.getElementById('field-detail-status');
      if (nameEl) nameEl.innerHTML = `🛰️ ${imgDate} · ${label}`;
      if (statusEl) {
        statusEl.innerHTML = mean != null ? (mean >= 0.4 ? '🟢 HEALTHY' : mean >= 0.2 ? '🟡 STRESSED' : '🔴 SEVERE STRESS') : '⚪ NO DATA';
        statusEl.style.color = color;
        statusEl.style.background = color + '22';
      }
    }

    // Yield Prediction Logic
    const yieldEl = document.getElementById('proj-yield');
    const revenueEl = document.getElementById('proj-revenue');
    const helperEl = document.getElementById('proj-helper');

    const areaEl = document.getElementById('field-detail-area');
    let areaAcres = 0;
    if (areaEl && areaEl.textContent && areaEl.textContent.includes('acres')) {
      areaAcres = parseFloat(areaEl.textContent.split(' ')[0]);
    } else if (window.FIELDS && window.FIELDS['SAT'] && window.FIELDS['SAT'].area) {
      areaAcres = parseFloat(window.FIELDS['SAT'].area.split(' ')[0]);
    }

    if (areaAcres > 0 && mean != null) {
      const baseYieldPerAcre = 15; // Wheat base
      const healthFactor = Math.min(1.2, Math.max(0.2, mean / 0.6));
      const projectedYield = areaAcres * baseYieldPerAcre * healthFactor;
      const marketPricePerQuintal = 2500; // Live APMC Mock
      const projectedRevenue = projectedYield * marketPricePerQuintal;

      if (yieldEl) yieldEl.textContent = projectedYield.toFixed(1) + ' Qtl';
      if (revenueEl) revenueEl.textContent = '₹' + projectedRevenue.toLocaleString('en-IN', { maximumFractionDigits: 0 });
      if (helperEl) helperEl.innerHTML = `Based on <b>${areaAcres.toFixed(1)} acres</b> of Wheat at <b>₹${marketPricePerQuintal}/q</b> (adjusted for ${(healthFactor*100).toFixed(0)}% crop health).`;
    } else {
      if (yieldEl) yieldEl.textContent = '—';
      if (revenueEl) revenueEl.textContent = '—';
      if (helperEl) helperEl.textContent = 'Area or health data missing for projection.';
    }

    window.toast(`🛰️ NDVI:${mean != null ? mean.toFixed(3) : 'N/A'} | 🌍 Soil:${soilMoisture || '--'}% | 💧 Rain:${totalRain != null ? totalRain.toFixed(1) : '--'}mm`);

    // Sync the analyzed field into the region list
    syncAnalyzedFieldToRegionList(mean, color, label, soilMoisture, totalRain, imgDate);
  }

  function syncAnalyzedFieldToRegionList(mean, color, label, soilMoisture, totalRain, imgDate) {
    if (typeof window.FIELDS === 'undefined') return;

    // Get real area computed earlier
    const areaEl = document.getElementById('field-detail-area');
    const area = (areaEl && areaEl.textContent && areaEl.textContent !== '—') ? areaEl.textContent : 'Calculating...';

    // Determine status key from NDVI
    const statusKey = mean == null ? 'unknown' : mean >= 0.4 ? 'healthy' : mean >= 0.2 ? 'stressed' : 'alert';
    const statusLabel = mean == null ? '⚪ NO DATA' : mean >= 0.4 ? '🟢 HEALTHY' : mean >= 0.2 ? '🟡 STRESSED' : '🔴 ALERT';

    // Upsert a "Satellite Field" entry in FIELDS keyed by 'SAT'
    window.FIELDS['SAT'] = {
      name: '🛰️ Satellite Field (' + imgDate + ')',
      crop: 'Not Set', // User hasn't set crop yet
      icon: '🌍',
      area: area,
      planted: soilMoisture ? 'Soil: ' + soilMoisture + '%' : '—',
      status: statusKey,
      statusLabel: statusLabel,
      ndvi: mean != null ? mean.toFixed(3) : null,
      rain7d: totalRain != null ? totalRain.toFixed(1) + 'mm' : null,
      _isSatellite: true
    };

    // Re-render region list to include satellite field at top
    const el = document.getElementById('region-list');
    if (!el) return;

    const allFields = window.FIELDS;
    const dotColors = {
      healthy: '#3d7a3a', stressed: '#f59e0b',
      irrigating: '#5ba4cf', harvesting: '#d4952a',
      alert: '#c0392b', unknown: '#94a3b8'
    };

    el.innerHTML = Object.keys(allFields).map(function(id) {
      const f = allFields[id];
      const dot = dotColors[f.status] || '#3d7a3a';
      const extraLine = f._isSatellite
        ? `${f.ndvi ? '📊 NDVI:' + f.ndvi + ' · ' : ''}${f.rain7d ? '💧 ' + f.rain7d : ''}`
        : `${f.icon} ${f.crop} · ${f.area}`;
      const bg = id === 'SAT' ? 'rgba(0,229,255,0.06)' : '';
      const border = id === 'SAT' ? 'border-left:3px solid #00e5ff;' : '';
      return `<div class="region-item" id="region-${id}" onclick="selectField('${id}')"
        style="padding:12px 16px;border-bottom:1px solid var(--border);cursor:pointer;display:flex;align-items:center;gap:12px;transition:.15s;background:${bg};${border}"
        onmouseover="this.style.background='rgba(61,122,58,0.05)'" onmouseout="this.style.background='${bg}'">
        <div style="width:10px;height:10px;border-radius:50%;background:${dot};flex-shrink:0;"></div>
        <div style="flex:1;min-width:0;">
          <div style="font-weight:700;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${f.name}</div>
          <div style="font-size:11px;color:var(--muted);margin-top:2px;">${extraLine}</div>
        </div>
        <div style="font-size:11px;font-weight:700;color:${dot};">${id}</div>
      </div>`;
    }).join('');

    // Highlight the satellite field
    const satRow = document.getElementById('region-SAT');
    if (satRow) satRow.style.background = 'rgba(0,229,255,0.08)';
  }

})();
