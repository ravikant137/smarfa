import re

with open("web/index.html", "r") as f:
    content = f.read()

# 1. Update CSS Variables & Font
old_vars = """  --bg:#0F172A;--surface:#1E293B;--card:#334155;--border:#475569;
  --green:#10B981;--green-l:#34D399;--green-d:#065F46;
  --yellow:#F59E0B;--red:#EF4444;--blue:#3B82F6;--purple:#8B5CF6;--cyan:#06B6D4;
  --text:#F1F5F9;--muted:#94A3B8;--white:#fff;"""
new_vars = """  --bg:#f5f7fa;--surface:#ffffff;--card:#f8fafc;--border:#e2e8f0;
  --green:#4CAF50;--green-l:#81c784;--green-d:#2e7d32;
  --yellow:#f59e0b;--red:#ef4444;--blue:#003366;--purple:#8b5cf6;--cyan:#06b6d4;
  --text:#1a1a2e;--muted:#64748b;--white:#fff;"""
content = content.replace(old_vars, new_vars)

content = content.replace("font-family:'Segoe UI'", "font-family:'Inter','Segoe UI'")

# 2. Add Top Header layout instead of Sidebar & Animations
old_app_css = """.app{max-width:1400px;margin:0 auto;height:100vh;display:none;flex-direction:row;position:relative;overflow:hidden}
.app.visible{display:flex}
.header{display:none;}

.nav{display:flex;flex-direction:column;width:240px;background:var(--surface);border-right:1px solid var(--border);position:relative;z-index:100;padding:24px 16px;gap:8px;}
.nav::before { content: '🌱 Smarfa'; display:block; font-size:24px; font-weight:800; color:var(--white); margin-bottom:32px; padding-left:12px; }
.nav button{width:100%;padding:12px 16px;background:none;border:none;color:var(--muted);font-size:15px;font-weight:600;cursor:pointer;display:flex;flex-direction:row;align-items:center;gap:12px;transition:.2s;border-radius:var(--radius-sm)}
.nav button:hover { background: rgba(16,185,129,.1); color: var(--text); }
.nav button.active{color:var(--white); background: var(--green); box-shadow:0 4px 12px rgba(16,185,129,.3)}
.nav button.active::after{display:none;}
.nav svg{width:22px;height:22px}

.content{flex:1;overflow-y:auto;padding:32px 48px;background:var(--bg);-webkit-overflow-scrolling:touch}"""

new_app_css = """.app{width:100%;min-height:100vh;display:none;flex-direction:column;position:relative;background:var(--bg);}
.app.visible{display:flex}
.header{display:none;}

/* Anjaneya-style Top Nav */
.top-banner { background: var(--green-d); color: #fff; text-align: center; padding: 6px; font-size: 11px; font-weight: bold; letter-spacing: 0.5px; }
.nav { display:flex; flex-direction:row; justify-content:space-between; align-items:center; padding: 16px 48px; background: rgba(255,255,255,0.9); backdrop-filter: blur(10px); border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 1000; box-shadow: 0 4px 20px rgba(0,0,0,0.03); }
.nav-logo { display:flex; align-items:center; gap: 12px; font-size: 24px; font-weight: 900; color: var(--blue); letter-spacing: -0.5px; }
.nav-logo span { color: var(--green); font-size: 10px; tracking: 2px; text-transform: uppercase; font-weight: 800; }
.nav-links { display:flex; gap: 32px; }
.nav-links button { background: none; border: none; font-size: 15px; font-weight: 700; color: var(--muted); cursor: pointer; transition: 0.2s; position: relative; padding: 8px 0; }
.nav-links button:hover { color: var(--green-d); }
.nav-links button.active { color: var(--green-d); }
.nav-links button.active::after { content:''; position:absolute; bottom:0; left:0; width:100%; height:3px; background:var(--green-d); border-radius: 4px; }
.nav-links button svg { display: none; } /* Hide icons in top nav */

.content{flex:1; max-width:1400px; margin: 0 auto; width: 100%; padding:40px 48px; overflow-y:visible;}

/* Hero Section override */
.welcome-banner { background: linear-gradient(135deg, #eef2ff 0%, #e8f5e9 30%, #ffffff 70%); border: 1px solid var(--border); box-shadow: 0 10px 30px rgba(0,0,0,0.05); padding: 60px 48px; }
.welcome-banner h2 { font-size: 48px; color: var(--blue); font-weight: 900; line-height: 1.1; margin-bottom: 12px; }
.welcome-banner h2 span { color: var(--green); }
.welcome-banner p { color: var(--muted); font-size: 18px; font-weight: 500; }
.welcome-banner::after { display: none; }

/* Scan Area / Prescription Upload style */
.scan-area { background: #fff; border: 2px dashed #cbd5e1; padding: 60px 40px; box-shadow: 0 4px 20px rgba(0,0,0,0.02); }
.scan-area:hover { border-color: var(--blue); background: #f8fafc; }
.scan-area .icon { font-size: 56px; margin-bottom: 16px; }

/* Cards & Buttons */
.stat-card, .result-card, .pump-card, .info-card { box-shadow: 0 4px 20px rgba(0,0,0,0.04); border: 1px solid var(--border); background: #fff; }
.stat-card .value { color: var(--blue); font-size: 28px; }
.btn-primary { background: var(--blue); color: #fff; }
.btn-primary:hover { background: #002244; transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,51,102,0.2); }
.scan-btns .btn:first-child { background: var(--green-d); }

/* ── Dynamic Animations ── */
@keyframes fadeInSlideUp {
  0% { opacity: 0; transform: translateY(20px); }
  100% { opacity: 1; transform: translateY(0); }
}
.tab.active { animation: fadeInSlideUp 0.5s ease-out forwards; }
.result-card { animation: fadeInSlideUp 0.5s ease-out forwards; animation-fill-mode: both; }
.result-card:nth-child(1) { animation-delay: 0.1s; }
.result-card:nth-child(2) { animation-delay: 0.2s; }
.result-card:nth-child(3) { animation-delay: 0.3s; }
.result-card:nth-child(4) { animation-delay: 0.4s; }

.stat-card, .action-btn, .pump-card, .info-card { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.stat-card:hover, .info-card:hover, .pump-card:hover { transform: translateY(-6px); box-shadow: 0 12px 24px rgba(0,0,0,0.1); border-color: var(--blue); }
.action-btn:hover { transform: translateX(6px); box-shadow: 0 8px 16px rgba(0,0,0,0.08); background: #f8fafc; }

@keyframes pulseHighlight {
  0% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.4); }
  70% { box-shadow: 0 0 0 15px rgba(76, 175, 80, 0); }
  100% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0); }
}
.btn-primary { position: relative; overflow: hidden; }
.btn-primary:active::after { content: ''; position: absolute; inset: 0; background: rgba(255,255,255,0.2); animation: pulseHighlight 0.6s ease-out; }
"""
content = content.replace(old_app_css, new_app_css)

# 3. Update HTML Structure for Nav
old_nav_html = """  <div class="header">
    <h1>🌱 Smarfa</h1>
    <p>Smart AI Farming Dashboard</p>
  </div>"""

new_nav_html = """  <div class="top-banner">🚚 AI Crop Diagnostics | Fast &amp; Accurate Results Within Seconds</div>
  <nav class="nav">
    <div class="nav-logo">
      <div style="background:#fff; border-radius:12px; padding:6px; box-shadow:0 4px 12px rgba(0,0,0,0.1); display:flex;">🌱</div>
      <div style="display:flex; flex-direction:column;">
        <div>SMARFA</div>
        <span>Diagnostics</span>
      </div>
    </div>
    <div class="nav-links">
      <button onclick="switchTab('dashboard')" class="active" id="btn-dashboard">Home</button>
      <button onclick="switchTab('scan')" id="btn-scan">AI Scan</button>
      <button onclick="switchTab('reports')" id="btn-reports">Reports</button>
      <button onclick="switchTab('alerts')" id="btn-alerts">Alerts</button>
      <button onclick="switchTab('profile')" id="btn-profile">Account</button>
    </div>
    <div class="nav-cta hidden lg:flex">
      <button class="btn btn-primary btn-sm" onclick="switchTab('scan')" style="padding:10px 24px; border-radius:8px;">Start Scan</button>
    </div>
  </nav>"""
content = content.replace(old_nav_html, new_nav_html)

# Remove the bottom nav completely
content = re.sub(r'<nav class="nav">.*?</nav>', '', content, flags=re.DOTALL)

# 4. Update the Welcome Banner to match Anjaneya's Hero
old_welcome = """      <div class="welcome-banner">
        <h2>Welcome, <span id="dash-username">Farmer</span> 👋</h2>
        <p>Your crops are monitored 24/7 with AI</p>
      </div>"""
new_welcome = """      <div class="welcome-banner">
        <p style="color:var(--green-d); font-size:14px; font-weight:700; text-transform:uppercase; margin-bottom:16px;">Your Trusted AI Agronomist</p>
        <h2 id="dash-username">Fast &amp; Accurate<br/><span>Crop Analysis</span> Near You</h2>
        <p style="margin-top:16px;">Upload a leaf photo and get an expert diagnostic within seconds.</p>
        <div style="margin-top:32px; display:flex; gap:16px;">
          <button class="btn btn-primary" onclick="switchTab('scan')" style="width:auto; padding:16px 32px;"><span style="font-size:20px;">📷</span> Start AI Scan</button>
          <button class="btn btn-outline" onclick="switchTab('reports')" style="width:auto; padding:16px 32px; border-color:var(--green-d); color:var(--green-d);">View Reports</button>
        </div>
      </div>"""
content = content.replace(old_welcome, new_welcome)

# 5. Inject History tracking logic
js_to_add = """
// ── Global State for History ──
let scanHistory = JSON.parse(localStorage.getItem('smarfaScanHistory')) || [];

function saveScan(data) {
  scanHistory.unshift({
    timestamp: new Date().toISOString(),
    crop: data.crop_detected || "Unknown Crop",
    severity: data.severity || "healthy",
    disease: (data.structured && data.structured.disease && data.structured.disease.name) ? data.structured.disease.name : (data.disease || "No disease")
  });
  if (scanHistory.length > 50) scanHistory.pop();
  localStorage.setItem('smarfaScanHistory', JSON.stringify(scanHistory));
  
  // Auto-generate alert
  if (data.severity === 'critical' || data.severity === 'warning') {
    let newAlert = {
      id: "scan-" + Date.now(),
      type: "crop_" + data.severity,
      message: `AI detected ${data.severity} issue: ${data.crop_detected} has ${data.structured?.disease?.name || 'disease symptoms'}.`,
      timestamp: new Date().toISOString()
    };
    let alerts = JSON.parse(localStorage.getItem('smarfaAlerts')) || [];
    alerts.unshift(newAlert);
    localStorage.setItem('smarfaAlerts', JSON.stringify(alerts));
  }
}
"""
content = content.replace("let imageBase64 = null;", "let imageBase64 = null;\n" + js_to_add)
content = content.replace("if (!r.ok) throw new Error(d.detail || 'Analysis failed');\n    renderResults(d);", "if (!r.ok) throw new Error(d.detail || 'Analysis failed');\n    saveScan(d);\n    renderResults(d);")

# 6. Overhaul loadReports to inject scanHistory
reports_override = """    var listEl = document.getElementById('r-scan-list');
    if (scanHistory.length === 0) {
      listEl.innerHTML = '<div class="empty-state"><div class="icon">🔍</div><p>No scans yet. Try taking a photo!</p></div>';
      document.getElementById('scan-history-card').style.display = 'block';
    } else {
      var html = '<div style="margin-bottom:16px; font-weight:bold; color:var(--blue); font-size:18px;">Recent AI Diagnoses</div>';
      var critCount = 0;
      scanHistory.forEach(h => {
        if(h.severity === 'critical') critCount++;
        let icon = h.severity==='healthy' ? '✅' : (h.severity==='warning' ? '⚠️' : '🚨');
        let dDate = new Date(h.timestamp).toLocaleString();
        html += `<div class="result-card" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
          <div>
            <div style="font-weight:700; color:var(--blue);">${icon} ${h.crop}</div>
            <div style="font-size:12px; color:var(--muted);">${h.disease}</div>
          </div>
          <div style="font-size:11px; color:var(--muted); text-align:right;">
             ${dDate}
          </div>
        </div>`;
      });
      listEl.innerHTML = html;
      document.getElementById('scan-history-card').style.display = 'block';
      
      if(scanHistory.length > 0) {
        let healthyPercent = Math.max(0, 100 - (critCount / scanHistory.length * 100));
        let cColor = healthyPercent >= 70 ? '#10B981' : healthyPercent >= 40 ? '#F59E0B' : '#EF4444';
        let hDeg = Math.round(healthyPercent / 100 * 360);
        document.getElementById('report-health-ring').style.background = 'conic-gradient(' + cColor + ' 0deg, ' + cColor + ' ' + hDeg + 'deg, #334155 ' + hDeg + 'deg)';
        document.getElementById('report-health-score').textContent = Math.round(healthyPercent);
      }
    }"""
content = re.sub(r'if \(d\.recent_scans && d\.recent_scans\.length > 0\) \{.*?\} else \{\s*document\.getElementById\(\'scan-history-card\'\)\.style\.display = \'none\';\s*\}', reports_override, content, flags=re.DOTALL)

with open("web/index.html", "w") as f:
    f.write(content)

print("Redesign applied successfully.")
