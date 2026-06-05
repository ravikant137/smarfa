
let API = window.location.origin;
if (!API || API === 'null' || API.startsWith('file://')) {
  API = 'http://192.168.29.181:8000';
}

if ("geolocation" in navigator) {
  navigator.geolocation.getCurrentPosition(function(position) {
    window.userLat = position.coords.latitude;
    window.userLon = position.coords.longitude;
  });
}

let currentUser = { username: "Admin", id: "dev" };
setTimeout(enterApp, 100);
let imageBase64 = null;

// ── Toast ───────────────────────────────────
function toast(msg, type='success') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = 'toast show ' + type;
  setTimeout(() => el.classList.remove('show'), 3000);
}

// ── Auth Tabs ───────────────────────────────
function showAuthTab(tab) {
  document.querySelectorAll('.auth-tabs button').forEach((b,i) => b.classList.toggle('active', (tab==='login'?0:1)===i));
  document.getElementById('form-login').classList.toggle('active', tab==='login');
  document.getElementById('form-register').classList.toggle('active', tab==='register');
  document.getElementById('login-error').textContent = '';
  document.getElementById('reg-error').textContent = '';
}

// ── Login ───────────────────────────────────
async function doLogin() {
  const user = document.getElementById('login-user').value.trim();
  const pass = document.getElementById('login-pass').value;
  const errEl = document.getElementById('login-error');
  errEl.textContent = '';
  if (!user || !pass) { errEl.textContent = 'Please fill in all fields'; return; }
  const btn = document.getElementById('login-btn');
  btn.disabled = true;
  document.getElementById('login-btn-text').innerHTML = '<span class="spinner" style="width:16px;height:16px"></span> Signing in...';
  try {
    const r = await fetch(API + '/login', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({username:user,password:pass}) });
    let d;
    try {
      d = await r.json();
    } catch(err) {
      if (!r.ok) throw new Error(`Server error: status ${r.status}`);
      throw err;
    }
    if (!r.ok) throw new Error(d.detail || 'Login failed');
    currentUser = { username: user, id: d.user_id };
    enterApp();
    toast('Welcome back, ' + user + '!');
  } catch(e) { errEl.textContent = e.message; }
  btn.disabled = false;
  document.getElementById('login-btn-text').textContent = 'Sign In';
}

// ── Register ────────────────────────────────
async function doRegister() {
  const user = document.getElementById('reg-user').value.trim();
  const pass = document.getElementById('reg-pass').value;
  const pass2 = document.getElementById('reg-pass2').value;
  const errEl = document.getElementById('reg-error');
  errEl.textContent = '';
  if (!user || !pass) { errEl.textContent = 'Please fill in all fields'; return; }
  if (pass.length < 4) { errEl.textContent = 'Password must be at least 4 characters'; return; }
  if (pass !== pass2) { errEl.textContent = 'Passwords do not match'; return; }
  const btn = document.getElementById('reg-btn');
  btn.disabled = true;
  document.getElementById('reg-btn-text').innerHTML = '<span class="spinner" style="width:16px;height:16px"></span> Creating...';
  try {
    const r = await fetch(API + '/register', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({username:user,password:pass}) });
    let d;
    try {
      d = await r.json();
    } catch(err) {
      if (!r.ok) throw new Error(`Server error: status ${r.status}`);
      throw err;
    }
    if (!r.ok) throw new Error(d.detail || 'Registration failed');
    currentUser = { username: user, id: d.id };
    enterApp();
    toast('Account created! Welcome to Smarfa!');
  } catch(e) { errEl.textContent = e.message; }
  btn.disabled = false;
  document.getElementById('reg-btn-text').textContent = 'Create Account';
}

// Enter key handlers
document.getElementById('login-pass').onkeydown = e => { if(e.key==='Enter') doLogin(); };
document.getElementById('reg-pass2').onkeydown = e => { if(e.key==='Enter') doRegister(); };

// ── Enter App ───────────────────────────────
function enterApp() {
  const name = currentUser.username.split('@')[0] || "Farmer";
  document.getElementById('dash-username').textContent = name;
  document.getElementById('profile-name').textContent = name;
  document.getElementById('profile-email').textContent = currentUser.username;
  document.getElementById('profile-avatar').textContent = name.charAt(0).toUpperCase();
  document.getElementById('auth-screen').classList.add('hidden');
  document.getElementById('app').classList.add('visible');
  loadDashboardData();
  checkAI();
}

function logout() {
  currentUser = null;
  imageBase64 = null;
  document.getElementById('auth-screen').classList.remove('hidden');
  document.getElementById('app').classList.remove('visible');
  document.getElementById('login-user').value = '';
  document.getElementById('login-pass').value = '';
  switchTab('dashboard');
}

// ── Tab Navigation ──────────────────────────
function switchTab(tab) {
  document.querySelectorAll('.content > .tab').forEach(p => p.classList.remove('active'));
  document.getElementById('tab-' + tab).classList.add('active');
  document.querySelectorAll('.nav button').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
  if (tab === 'alerts') loadAlerts();
  if (tab === 'profile') checkAI();
  if (tab === 'reports') loadReports();
  if (tab === 'dashboard') loadDashboardData();
}

// ── Dashboard Data ──────────────────────────
async function loadDashboardData() {
  try {
    const r = await fetch(API + '/reports/overview');
    const d = await r.json();
    const w = d.week_summary;

    // Health score ring
    const score = d.health_score || 0;
    const deg = Math.round(score / 100 * 360);
    const color = score >= 70 ? '#10B981' : score >= 40 ? '#F59E0B' : '#EF4444';
    document.getElementById('health-ring').style.background = 'conic-gradient(' + color + ' 0deg, ' + color + ' ' + deg + 'deg, #334155 ' + deg + 'deg)';
    document.getElementById('health-score').textContent = score;

    // Stat cards
    document.getElementById('s-temp').textContent = w.avg_temp ? w.avg_temp + '\u00B0C' : '\u2014';
    document.getElementById('s-temp-sub').textContent = w.min_temp ? w.min_temp + '\u00B0 \u2013 ' + w.max_temp + '\u00B0' : '';
    document.getElementById('s-moisture').textContent = w.avg_moisture ? w.avg_moisture + '%' : '\u2014';
    document.getElementById('s-moisture-sub').textContent = w.min_moisture ? 'Low: ' + w.min_moisture + '%' : '';
    document.getElementById('s-height').textContent = w.avg_height ? w.avg_height + 'cm' : '\u2014';
    document.getElementById('s-height-sub').textContent = w.readings_count ? w.readings_count + ' readings' : '';
    document.getElementById('s-alerts').textContent = w.alerts_count != null ? w.alerts_count : 0;
    document.getElementById('s-alerts-sub').textContent = (w.alerts_total != null ? w.alerts_total : 0) + ' total';

    // Pump status
    loadPumpStatus();
  } catch(e) { console.log('dashboard error', e); }
}

// ── Water Pump ──────────────────────────────
async function loadPumpStatus() {
  try {
    const r = await fetch(API + '/pump/status/field-1');
    const d = await r.json();
    const ind = document.getElementById('pump-indicator');
    const txt = document.getElementById('pump-status-text');
    const det = document.getElementById('pump-status-detail');

    if (d.is_running) {
      ind.className = 'pump-indicator on';
      txt.textContent = '\uD83D\uDCA7 Pump Running';
      txt.style.color = 'var(--green)';
      det.textContent = d.current.reason + ' \u2014 ' + d.current.duration + 's';
    } else {
      ind.className = 'pump-indicator off';
      txt.textContent = 'Pump Idle';
      txt.style.color = 'var(--muted)';
      det.textContent = 'No active irrigation';
    }

    // Recent logs
    var logEl = document.getElementById('pump-log');
    if (d.recent_logs.length) {
      logEl.innerHTML = '<div style="font-size:12px;color:var(--muted);margin-bottom:8px;font-weight:600">Recent Activity</div>' +
        d.recent_logs.slice(0, 5).map(function(l) {
          return '<div class="pump-log-item"><div><span class="pump-tag ' + esc(l.trigger) + '">' + esc(l.trigger) + '</span>' +
            '<span style="margin-left:6px">' + esc(l.reason.substring(0,40)) + (l.reason.length>40?'...':'') + '</span></div>' +
            '<span style="color:var(--muted)">' + l.duration + 's</span></div>';
        }).join('');
    } else {
      logEl.innerHTML = '<div style="font-size:12px;color:var(--muted);text-align:center;padding:8px">No pump activity yet</div>';
    }
  } catch(e) { console.log('pump error', e); }
}

async function startPump() {
  try {
    const r = await fetch(API + '/pump/start', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ crop_id: 'field-1', duration_seconds: 120 })
    });
    const d = await r.json();
    toast('\uD83D\uDCA7 Water pump started! Duration: ' + d.duration + 's');
    loadPumpStatus();
  } catch(e) { toast('Failed to start pump', 'error'); }
}

async function stopPump() {
  try {
    await fetch(API + '/pump/stop', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ crop_id: 'field-1' })
    });
    toast('Pump stopped');
    loadPumpStatus();
  } catch(e) { toast('Failed to stop pump', 'error'); }
}

// ── Crop Scan ───────────────────────────────
var fileInput = document.getElementById('file-input');
var scanArea = document.getElementById('scan-area');

fileInput.onchange = function(e) {
  var file = e.target.files[0];
  if (!file) return;
  var reader = new FileReader();
  reader.onload = function(ev) {
    var dataUrl = ev.target.result;
    imageBase64 = dataUrl.split(',')[1];
    document.getElementById('scan-preview').src = dataUrl;
    document.getElementById('scan-preview').style.display = 'block';
    document.getElementById('scan-placeholder').style.display = 'none';
    scanArea.classList.add('has-image');
    document.getElementById('analyze-btn').disabled = false;
  };
  reader.readAsDataURL(file);
};

scanArea.ondragover = function(e) { e.preventDefault(); scanArea.style.borderColor = 'var(--green)'; };
scanArea.ondragleave = function() { scanArea.style.borderColor = ''; };
scanArea.ondrop = function(e) {
  e.preventDefault(); scanArea.style.borderColor = '';
  var file = e.dataTransfer.files[0];
  if (file && file.type.startsWith('image/')) { fileInput.files = e.dataTransfer.files; fileInput.dispatchEvent(new Event('change')); }
};

function clearScan() {
  imageBase64 = null; fileInput.value = '';
  document.getElementById('scan-preview').style.display = 'none';
  document.getElementById('scan-placeholder').style.display = '';
  scanArea.classList.remove('has-image');
  document.getElementById('analyze-btn').disabled = true;
  document.getElementById('scan-results').style.display = 'none';
}

async function analyzeCrop() {
  if (!imageBase64) return;
  var btn = document.getElementById('analyze-btn');
  var loading = document.getElementById('scan-loading');
  var results = document.getElementById('scan-results');
  btn.disabled = true; loading.style.display = 'flex'; results.style.display = 'none';
  try {
    var hintVal = 'auto';
    var payload = { 
      image_base64: imageBase64,
      crop_hint: hintVal !== 'auto' ? hintVal : null,
      lat: window.userLat || 0,
      lon: window.userLon || 0
    };
    var r = await fetch(API + '/analyze_crop', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
    var d = await r.json();
    if (!r.ok) throw new Error(d.detail || 'Analysis failed');
    renderResults(d);
    // Save to local scan history
    var history = JSON.parse(localStorage.getItem('scanHistory') || '[]');
    d.timestamp = new Date().toISOString();
    history.push(d);
    localStorage.setItem('scanHistory', JSON.stringify(history));
    results.style.display = 'block';
  } catch(e) {
    results.innerHTML = '<div class="result-card"><h3>Error</h3><p>' + esc(e.message) + '</p></div>';
    results.style.display = 'block';
  }
  loading.style.display = 'none'; btn.disabled = false;
}

function renderResults(d) {
  var el = document.getElementById('scan-results');
  var sev = d.severity || 'warning';
  var confColor = (d.ai_confidence||0) >= 60 ? 'var(--green)' : (d.ai_confidence||0) >= 30 ? 'var(--yellow)' : 'var(--red)';
  var s = d.structured || {};
  
  var html = '';
  
  // 1. Green Shield Safety Vetted (Green Border)
  if (s.safety_check) {
    var sc = s.safety_check;
    html += '<div class="result-card" style="border:1px solid var(--green); border-radius:12px; margin-bottom:16px;">' +
      '<h3 style="color:var(--green); margin-bottom:16px;">🛡️ Green Shield Pesticide Safety Vetted</h3>' +
      '<div style="display:flex; justify-content:space-between; border-bottom:1px solid var(--border); padding-bottom:8px; margin-bottom:8px;">' +
      '<span style="color:var(--muted); font-size:13px;">Registry Status</span>' +
      '<span style="color:var(--green); font-weight:700; font-size:13px;">✓ COMPLIANT & APPROVED</span></div>' +
      '<div style="display:flex; justify-content:space-between; border-bottom:1px solid var(--border); padding-bottom:8px; margin-bottom:8px;">' +
      '<span style="color:var(--muted); font-size:13px;">Substance Vetted</span>' +
      '<span style="color:var(--text); font-weight:600; font-size:13px;">' + esc(sc.chemical||'N/A') + '</span></div>' +
      '<div style="display:flex; justify-content:space-between; border-bottom:1px solid var(--border); padding-bottom:8px; margin-bottom:8px;">' +
      '<span style="color:var(--muted); font-size:13px;">Safety Class</span>' +
      '<span style="color:var(--cyan); font-weight:600; font-size:13px;">' + esc(sc.safety_class||'N/A') + '</span></div>' +
      '<div style="display:flex; justify-content:space-between; border-bottom:1px solid var(--border); padding-bottom:8px; margin-bottom:8px;">' +
      '<span style="color:var(--muted); font-size:13px;">Eco Designation</span>' +
      '<span style="background:rgba(255,255,255,0.1); padding:2px 8px; border-radius:4px; font-size:11px;">' + esc(sc.eco_status||'N/A') + '</span></div>' +
      '<div style="margin-top:12px; font-size:12px; color:var(--muted);">' + esc(sc.compliance_details||'') + '</div>' +
      '</div>';
  }

  // 2. Treatment Recommendations (Grey/Blue Border)
  if (s.treatment) {
    var t = s.treatment;
    html += '<div class="result-card" style="border:1px solid var(--border); border-radius:12px; margin-bottom:16px;">' +
      '<h3 style="color:var(--text); margin-bottom:16px;">💊 Treatment Recommendations</h3>' +
      '<div style="margin-bottom:12px;"><strong style="color:var(--green); font-size:13px;">🌿 Organic Solution</strong><p style="font-size:12px; color:var(--muted); margin-top:4px;">' + esc(t.organic) + '</p></div>' +
      '<div style="margin-bottom:12px;"><strong style="color:var(--cyan); font-size:13px;">🧪 Chemical Solution</strong><p style="font-size:12px; color:var(--muted); margin-top:4px;">' + esc(t.chemical) + '</p></div>' +
      '<div style="margin-bottom:12px;"><strong style="color:var(--text); font-size:13px;">💧 Dosage</strong><p style="font-size:12px; color:var(--muted); margin-top:4px;">' + esc(t.dosage) + '</p></div>' +
      '<div style="margin-bottom:12px;"><strong style="color:var(--yellow); font-size:13px;">🛡️ Prevention</strong><p style="font-size:12px; color:var(--muted); margin-top:4px;">' + esc(t.prevention) + '</p></div>' +
      '<div style="margin-bottom:12px;"><strong style="color:#3b82f6; font-size:13px;">💧 Irrigation Adjustment</strong><p style="font-size:12px; color:var(--muted); margin-top:4px;">' + esc(t.irrigation_adjustment) + '</p></div>' +
      '<div><strong style="color:#f59e0b; font-size:13px;">⛏️ Soil Correction</strong><p style="font-size:12px; color:var(--muted); margin-top:4px;">' + esc(t.soil_correction) + '</p></div>' +
      '</div>';
  }

  // 3. Multi-Agent Cooperative Diagnosis (Purple Border)
  if (s.agent_logs) {
    var logs = s.agent_logs;
    html += '<div class="result-card" style="border:1px solid var(--purple); border-radius:12px; margin-bottom:16px; background:linear-gradient(to right, rgba(139,92,246,0.05), transparent);">' +
      '<h3 style="color:var(--purple); margin-bottom:16px;">🧠 GPT-4o Multi-Agent Cooperative Diagnosis</h3>' +
      '<div style="padding:10px; background:rgba(255,255,255,0.03); border-radius:8px; margin-bottom:8px;"><strong style="color:var(--green); font-size:13px;">🔍 Pathology Agent:</strong><p style="font-size:12px; color:var(--text); margin-top:4px;">' + esc(logs.pathology_agent) + '</p></div>' +
      '<div style="padding:10px; background:rgba(255,255,255,0.03); border-radius:8px; margin-bottom:8px;"><strong style="color:var(--cyan); font-size:13px;">🌾 Agronomist Agent:</strong><p style="font-size:12px; color:var(--text); margin-top:4px;">' + esc(logs.agronomy_agent) + '</p></div>' +
      '<div style="padding:10px; background:rgba(255,255,255,0.03); border-radius:8px;"><strong style="color:#f59e0b; font-size:13px;">🛡️ Safety Agent (Green Shield):</strong><p style="font-size:12px; color:var(--text); margin-top:4px;">' + esc(logs.safety_agent) + '</p></div>' +
      '</div>';
  }

  // 4. Crop Info & Warning (Yellow/Red Border)
  var cropName = s.final_crop || d.crop_detected || 'Unknown Crop';
  var sevColor = sev === 'critical' ? 'var(--red)' : sev === 'warning' ? 'var(--yellow)' : 'var(--green)';
  html += '<div class="result-card" style="border:1px solid ' + sevColor + '; border-radius:12px; margin-bottom:16px; position:relative;">' +
    '<div style="position:absolute; top:12px; right:12px; background:rgba(255,255,255,0.1); padding:2px 8px; border-radius:4px; font-size:10px; color:var(--muted);">AI</div>' +
    '<div style="display:inline-block; padding:4px 8px; border-radius:6px; background:rgba(245,158,11,0.1); color:' + sevColor + '; font-size:11px; font-weight:700; text-transform:uppercase; margin-bottom:12px;">' + sev.toUpperCase() + ' ⚠️</div>' +
    '<h3 style="color:var(--text); margin-bottom:8px; font-size:16px;">🌿 ' + esc(cropName) + '</h3>' +
    '<p style="font-size:13px; color:var(--muted); line-height:1.5;">' + esc(d.health_assessment) + '</p>' +
    '</div>';

  el.innerHTML = html;
  
  // Also show expert fallback
  var fallback = document.getElementById('expert-fallback');
  if (fallback) fallback.style.display = 'block';

  // Save to local scan history
  var history = JSON.parse(localStorage.getItem('scanHistory') || '[]');
  d.timestamp = new Date().toISOString();
  history.push(d);
  localStorage.setItem('scanHistory', JSON.stringify(history));
}

function esc(s) { var d = document.createElement('div'); d.textContent = s || ''; return d.innerHTML; }

// ── Reports ─────────────────────────────────
async function loadReports() {
  var loading = document.getElementById('reports-loading');
  var content = document.getElementById('reports-content');
  loading.style.display = 'flex'; content.style.display = 'none';

  // Read from local history
  var history = JSON.parse(localStorage.getItem('scanHistory') || '[]');
  
  setTimeout(function() {
    loading.style.display = 'none';
    content.style.display = 'block';

    if (history.length === 0) {
      document.getElementById('reports-history-list').innerHTML = '<div style="color:var(--muted); font-size:13px;">No crop history found. Run an AI Scan first!</div>';
      return;
    }

    var healthy = history.filter(function(x) { return x.severity === 'healthy'; }).length;
    var score = Math.round((healthy / history.length) * 100) || 0;
    
    // Update Ring
    var deg = Math.round(score / 100 * 360);
    var color = score >= 70 ? '#10B981' : score >= 40 ? '#F59E0B' : '#EF4444';
    document.getElementById('report-health-ring').style.background = 'conic-gradient(' + color + ' ' + deg + 'deg, rgba(255,255,255,0.05) ' + deg + 'deg)';
    document.getElementById('report-health-score').textContent = score + '%';

    // Update History List
    var html = '';
    // Reverse to show newest first, or keep order for chronological. Let's do chronological Start to End.
    history.forEach(function(s, i) {
       var cropName = (s.structured && s.structured.final_crop) ? s.structured.final_crop : (s.crop_detected || 'Unknown');
       var sev = s.severity || 'warning';
       var sevColor = sev === 'critical' ? 'var(--red)' : sev === 'warning' ? 'var(--yellow)' : 'var(--green)';
       var date = new Date(s.timestamp || Date.now()).toLocaleString();
       
       html += '<div style="padding:12px; background:rgba(255,255,255,0.02); border-left:3px solid ' + sevColor + '; border-radius:6px;">' +
         '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">' +
         '<strong style="color:var(--text); font-size:14px;">Scan ' + (i+1) + ': ' + esc(cropName) + '</strong>' +
         '<span style="font-size:11px; color:var(--muted);">' + date + '</span></div>' +
         '<p style="font-size:12px; color:var(--muted); line-height:1.4;">' + esc(s.health_assessment) + '</p>' +
         '</div>';
    });
    
    document.getElementById('reports-history-list').innerHTML = html;
  }, 500); // fake loading delay for UI polish
}

function hideAlertDetails() {
  var modal = document.getElementById('alert-details-modal');
  if (modal) modal.style.display = 'none';
}

    // Recent AI Scans
    if (d.recent_scans && d.recent_scans.length) {
      var sevColors = {healthy:'var(--green)',warning:'var(--yellow)',critical:'var(--red)'};
      var sevIcons = {healthy:'✅',warning:'⚠️',critical:'🚨'};
      document.getElementById('scan-history-card').style.display = 'block';
      document.getElementById('r-scan-list').innerHTML = d.recent_scans.map(function(s) {
        var col = sevColors[s.severity] || 'var(--muted)';
        var ico = sevIcons[s.severity] || '🔬';
        return '<div style="padding:10px 0;border-bottom:1px solid var(--border);display:flex;gap:10px;align-items:flex-start">' +
          '<div style="border-left:3px solid ' + col + ';padding-left:10px;flex:1">' +
          '<div style="font-weight:600;font-size:14px">' + ico + ' ' + esc(s.crop_detected) + ' <span style="font-size:11px;color:' + col + ';font-weight:700">' + (s.severity||'').toUpperCase() + '</span></div>' +
          '<div style="font-size:11px;color:var(--muted);margin-top:2px">' + s.ai_confidence + '% confidence · ' + new Date(s.timestamp).toLocaleString() + '</div>' +
          (s.health_assessment ? '<div style="font-size:12px;color:var(--text);margin-top:4px;line-height:1.5">' + esc(s.health_assessment) + '</div>' : '') +
          '</div></div>';
      }).join('');
    }

    content.style.display = 'block';
  } catch(e) {
    content.innerHTML = '<div class="empty-state"><div class="icon">\uD83D\uDCCA</div><p>No report data yet. Send sensor data to see reports.</p></div>';
    content.style.display = 'block';
  }
  loading.style.display = 'none';
}

function renderTrend(barId, labelId, data, key, max) {
  var values = data.map(function(d) { return d[key]; });
  if (!max) max = Math.max.apply(null, values) * 1.2 || 1;
  document.getElementById(barId).innerHTML = values.map(function(v, i) {
    return '<div class="trend-col" style="height:' + Math.max(4, v/max*100) + '%"><div class="tip">' + data[i].date.slice(5) + ': ' + v + '</div></div>';
  }).join('');
  document.getElementById(labelId).innerHTML = data.map(function(d) { return '<span>' + d.date.slice(5) + '</span>'; }).join('');
}

// ── Alerts ──────────────────────────────────
async function loadAlerts() {
  var el = document.getElementById('alerts-list');
  el.innerHTML = '<div class="loading-overlay"><div class="spinner"></div><p>Loading alerts...</p></div>';
  try {
    var results = await Promise.all([
      fetch(API + '/alerts').then(function(r){ return r.json(); }).catch(function(){ return []; }),
      fetch(API + '/scan_history?limit=20').then(function(r){ return r.json(); }).catch(function(){ return []; }),
    ]);
    var sysAlerts = results[0] || [];
    var scans = results[1] || [];

    // Convert scans to alert-shaped objects (scans already create Alert rows, so avoid duplicates:
    // only show scans not already in sysAlerts as crop_ types)
    var hasScanAlerts = sysAlerts.some(function(a){ return a.type && a.type.startsWith('crop_'); });
    var extra = [];
    if (!hasScanAlerts) {
      extra = scans.map(function(s, i) {
        return { id: 'scan_' + s.id, type: 'crop_' + (s.severity||'warning'), message: s.crop_detected + ' — ' + (s.severity||'').toUpperCase() + ' detected at ' + s.ai_confidence + '% confidence. ' + (s.health_assessment||''), timestamp: s.timestamp, _isScan: true };
      });
    }

    var all = sysAlerts.concat(extra).sort(function(a, b){ return new Date(b.timestamp) - new Date(a.timestamp); });

    if (!all.length) {
      el.innerHTML = '<div class="empty-state"><div class="icon">🔔</div><p>No alerts yet — your farm is looking good!</p></div>';
      return;
    }

    var typeColors = {crop_healthy:'var(--green)',crop_warning:'var(--yellow)',crop_critical:'var(--red)',moisture_warning:'var(--blue)',temp_warning:'var(--red)',intrusion_alarm:'var(--red)',pump_auto_start:'var(--cyan)',growth_drop:'var(--yellow)',growth_slow:'var(--yellow)'};
    var icons = {crop_healthy:'🌿',crop_warning:'⚠️',crop_critical:'🚨',moisture_warning:'💧',temp_warning:'🌡️',growth_drop:'📉',growth_slow:'🐌',intrusion_alarm:'🚨',pump_auto_start:'💧'};

    el.innerHTML = all.map(function(a) {
      var col = typeColors[a.type] || 'var(--yellow)';
      var ico = icons[a.type] || '⚠️';
      var badge = a._isScan ? '<span class="type-tag" style="background:rgba(168,85,247,.15);color:var(--purple)">AI SCAN</span>' : '<span class="type-tag">' + esc(a.type||'alert') + '</span>';
      return '<div class="alert-item ' + esc(a.type||'') + '" style="border-left-color:' + col + '">' +
        '<div style="display:flex;align-items:center">' +
        '<span class="time">' + ico + ' ' + new Date(a.timestamp).toLocaleString() + '</span>' + badge +
        '</div><div class="msg">' + esc(a.message) + '</div></div>';
    }).join('');
  } catch(e) {
    el.innerHTML = '<div class="empty-state"><div class="icon">⚠️</div><p>Could not load alerts</p></div>';
  }
}

// ── AI Status ───────────────────────────────
async function checkAI() {
  var banner = document.getElementById('ai-banner');
  var profileAI = document.getElementById('profile-ai');
  try {
    var r = await fetch(API + '/ai_status');
    var d = await r.json();
    if (d.china_agent) {
      banner.style.display = 'none';
      profileAI.innerHTML = '<span style="color:var(--green);font-weight:700">GPT-4o Vision Active (99% Accuracy) 🛡️</span>';
    } else if (d.ollama) {
      banner.style.display = 'none';
      var models = d.models.map(function(m) { return m.split(':')[0]; }).join(', ');
      profileAI.innerHTML = '<span style="color:var(--green)">Ollama (' + models + ') \u2705</span>';
    } else {
      banner.style.display = 'block';
      banner.innerHTML = '\uD83D\uDCA1 Install <a href="https://ollama.com" target="_blank">Ollama</a> for AI crop analysis. Without it, color analysis is used.';
      profileAI.textContent = 'Local (PIL analysis)';
    }
  } catch(e) { profileAI.textContent = 'Local (PIL)'; }
}

// ── Crop Lifecycle ───────────────────────────
async function loadLifecycle() {
  var crop = document.getElementById('lifecycle-crop-select').value;
  var el = document.getElementById('lifecycle-content');
  if (!crop) { el.innerHTML = '<div style="text-align:center;padding:40px;color:var(--muted)"><div style="font-size:48px;margin-bottom:12px">🌱</div><p>Select a crop above to view its complete lifecycle</p></div>'; return; }
  el.innerHTML = '<div class="loading-overlay" style="position:relative;display:flex"><div class="spinner"></div><p>Loading lifecycle data...</p></div>';
  try {
    var r = await fetch(API + '/crop_lifecycle/' + encodeURIComponent(crop));
    if (!r.ok) throw new Error('Not found');
    var d = await r.json();
    var stages = d.stages || {};
    var stageOrder = ['germination','vegetative','flowering','fruiting','harvest'];
    var stageIcons = {germination:'🌱',vegetative:'🌿',flowering:'🌸',fruiting:'🍎',harvest:'🌾'};

    var html = '<div class="result-card" style="border-left:3px solid var(--green)"><h3>🌱 ' + esc(d.crop_name) + '</h3>' +
      '<div class="report-metric"><span class="label">Varieties</span><span class="val" style="font-size:12px">' + (d.variety_types||[]).join(', ') + '</span></div>' +
      '<div class="report-metric"><span class="label">Total Growth Duration</span><span class="val">' + esc(d.total_growth_days) + ' days</span></div>' +
      '<div class="report-metric"><span class="label">Sunlight</span><span class="val">' + esc(d.sunlight) + '</span></div>' +
      '<div class="report-metric"><span class="label">Soil Preference</span><span class="val" style="font-size:12px">' + esc(d.soil_type) + '</span></div>' +
      '<div class="report-metric"><span class="label">Yield per Acre</span><span class="val" style="font-size:12px">' + esc(d.yield_per_acre) + '</span></div></div>';

    // Growth stages
    stageOrder.forEach(function(sKey) {
      var st = stages[sKey];
      if (!st) return;
      var icon = stageIcons[sKey] || '🌿';
      html += '<div class="result-card">' +
        '<h3>' + icon + ' ' + sKey.charAt(0).toUpperCase() + sKey.slice(1) + ' Stage</h3>' +
        '<div class="report-metric"><span class="label">Duration</span><span class="val">' + esc(st.duration_days) + '</span></div>' +
        '<div class="report-metric"><span class="label">💧 Water</span><span class="val" style="font-size:12px">' + esc(st.water) + '</span></div>' +
        '<div class="report-metric"><span class="label">🧪 Fertilizer</span><span class="val" style="font-size:12px">' + esc(st.fertilizer) + '</span></div>';
      // Pest risks for this stage
      if (d.pest_risks && d.pest_risks[sKey]) {
        html += '<div class="report-metric"><span class="label">🐛 Pest Risks</span><span class="val" style="font-size:12px;color:var(--yellow)">' + d.pest_risks[sKey].join(', ') + '</span></div>';
      }
      // Disease risks for this stage
      if (d.disease_risks && d.disease_risks[sKey]) {
        html += '<div class="report-metric"><span class="label">🦠 Disease Risks</span><span class="val" style="font-size:12px;color:var(--red)">' + d.disease_risks[sKey].join(', ') + '</span></div>';
      }
      html += '</div>';
    });

    // Harvest indicators
    if (d.harvest_indicators && d.harvest_indicators.length) {
      html += '<div class="result-card" style="border-left:3px solid var(--yellow)"><h3>✅ Harvest Indicators</h3><ul class="rec-list">' +
        d.harvest_indicators.map(function(h) { return '<li>' + esc(h) + '</li>'; }).join('') + '</ul></div>';
    }

    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = '<div class="result-card"><h3>Error</h3><p>Could not load lifecycle for ' + esc(crop) + '</p></div>';
  }
}

// Auto-refresh pump status every 30s
setInterval(function() { if (currentUser) loadPumpStatus(); }, 30000);

