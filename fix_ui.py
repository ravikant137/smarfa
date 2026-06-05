import re

with open("web/index.html", "r") as f:
    content = f.read()

# 1. Force replace the entire CSS block
new_css = """*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#f5f7fa;--surface:#ffffff;--card:#f8fafc;--border:#e2e8f0;
  --green:#4CAF50;--green-l:#81c784;--green-d:#2e7d32;
  --yellow:#f59e0b;--red:#ef4444;--blue:#003366;--purple:#8b5cf6;--cyan:#06b6d4;
  --text:#1a1a2e;--muted:#64748b;--white:#fff;
  --radius:14px;--radius-sm:10px;
  --shadow:0 4px 24px rgba(0,0,0,.08);
}
body{font-family:'Inter','Segoe UI',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;overflow-x:hidden}
a{color:var(--green);text-decoration:none}
button{font-family:inherit}

/* ── Full-screen auth overlay ──────── */
.auth-screen{display:none !important;}

/* ── App Layout ───────────────────── */
.app{width:100%;min-height:100vh;display:flex;flex-direction:column;position:relative;background:var(--bg);}
.header{display:none;}

/* Anjaneya-style Top Nav */
.top-banner { background: var(--green-d); color: #fff; text-align: center; padding: 6px; font-size: 11px; font-weight: bold; letter-spacing: 0.5px; }
.nav { display:flex; flex-direction:row; justify-content:space-between; align-items:center; padding: 16px 48px; background: rgba(255,255,255,0.9); backdrop-filter: blur(10px); border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 1000; box-shadow: 0 4px 20px rgba(0,0,0,0.03); }
.nav-logo { display:flex; align-items:center; gap: 12px; font-size: 24px; font-weight: 900; color: var(--blue); letter-spacing: -0.5px; }
.nav-logo span { color: var(--green); font-size: 10px; letter-spacing: 2px; text-transform: uppercase; font-weight: 800; }
.nav-links { display:flex; gap: 32px; }
.nav-links button { background: none; border: none; font-size: 15px; font-weight: 700; color: var(--muted); cursor: pointer; transition: 0.2s; position: relative; padding: 8px 0; }
.nav-links button:hover { color: var(--green-d); }
.nav-links button.active { color: var(--green-d); }
.nav-links button.active::after { content:''; position:absolute; bottom:0; left:0; width:100%; height:3px; background:var(--green-d); border-radius: 4px; }
.nav-links button svg { display: none; } /* Hide icons in top nav */

.content{flex:1; max-width:1400px; margin: 0 auto; width: 100%; padding:40px 48px; overflow-y:visible;}
.tab{display:none}.tab.active{display:block}

/* ── Dashboard ────────────────────── */
.health-ring{width:120px;height:120px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 16px;position:relative}
.health-ring .score{font-size:36px;font-weight:800; color:var(--text)}

/* Hero Section override */
.welcome-banner { background: linear-gradient(135deg, #eef2ff 0%, #e8f5e9 30%, #ffffff 70%); border: 1px solid var(--border); box-shadow: 0 10px 30px rgba(0,0,0,0.05); padding: 60px 48px; margin-bottom:16px; border-radius:var(--radius); position:relative; overflow:hidden;}
.welcome-banner h2 { font-size: 48px; color: var(--blue); font-weight: 900; line-height: 1.1; margin-bottom: 12px; }
.welcome-banner h2 span { color: var(--green); }
.welcome-banner p { color: var(--muted); font-size: 18px; font-weight: 500; }
.welcome-banner::after { display: none; } /* remove old emoji */

.stat-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:16px}
.stat-card{background:var(--surface);border-radius:var(--radius-sm);padding:14px;border:1px solid var(--border);transition:.2s}
.stat-card:hover{border-color:var(--green);transform:translateY(-2px)}
.stat-card .icon{font-size:24px;margin-bottom:6px}
.stat-card .label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px}
.stat-card .value{font-size:20px;font-weight:700;margin-top:2px;color:var(--blue)}
.stat-card .sub{font-size:11px;color:var(--muted);margin-top:2px}
.section-title{font-size:16px;font-weight:700;margin:20px 0 12px;display:flex;align-items:center;gap:8px}

.btn{width:100%;padding:14px;border:none;border-radius:var(--radius-sm);font-size:15px;font-weight:600;cursor:pointer;transition:.2s;display:flex;align-items:center;justify-content:center;gap:8px}
.btn-primary{background:var(--blue);color:var(--white)}
.btn-primary:hover{background:#002244;transform:translateY(-2px);box-shadow:0 8px 20px rgba(0,51,102,.2)}
.btn-outline{background:transparent;color:var(--green);border:1.5px solid var(--green)}
.btn-outline:hover{background:rgba(16,185,129,.08)}
.btn-sm{padding:10px 16px;width:auto;font-size:13px;border-radius:8px}

/* Scan Area */
.scan-area { background: #fff; border: 2px dashed #cbd5e1; padding: 60px 40px; box-shadow: 0 4px 20px rgba(0,0,0,0.02); text-align:center; border-radius:var(--radius); margin-bottom:16px;}
.scan-area:hover { border-color: var(--blue); background: #f8fafc; }
.scan-area .icon { font-size: 56px; margin-bottom: 16px; }

/* Dynamic Animations */
@keyframes fadeInSlideUp {
  0% { opacity: 0; transform: translateY(20px); }
  100% { opacity: 1; transform: translateY(0); }
}
.tab.active { animation: fadeInSlideUp 0.5s ease-out forwards; }
.result-card, .pump-card, .info-card { background: #fff; box-shadow: 0 4px 20px rgba(0,0,0,0.04); border: 1px solid var(--border); border-radius: var(--radius); padding:20px; margin-bottom:12px; animation: fadeInSlideUp 0.5s ease-out forwards; animation-fill-mode: both; transition: all 0.3s;}
.result-card:hover, .info-card:hover { transform: translateY(-6px); box-shadow: 0 12px 24px rgba(0,0,0,0.1); border-color: var(--blue); }

@keyframes pulseHighlight {
  0% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.4); }
  70% { box-shadow: 0 0 0 15px rgba(76, 175, 80, 0); }
  100% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0); }
}
.btn-primary:active::after { content: ''; position: absolute; inset: 0; background: rgba(255,255,255,0.2); animation: pulseHighlight 0.6s ease-out; }

.error-msg{color:var(--red);font-size:13px;margin-top:10px;text-align:center;min-height:20px}
.loading-overlay{display:none;flex-direction:column;align-items:center;justify-content:center;padding:40px}
.spinner{width:40px;height:40px;border:4px solid rgba(16,185,129,.2);border-top-color:var(--green);border-radius:50%;animation:spin 1s linear infinite;margin-bottom:16px}
@keyframes spin{to{transform:rotate(360deg)}}
.alert-item{background:var(--surface);border-left:4px solid;border-radius:var(--radius-sm);padding:14px;margin-bottom:10px;box-shadow:var(--shadow)}
.alert-item.critical{border-color:var(--red)}
.alert-item.warning{border-color:var(--yellow)}
.alert-item.info{border-color:var(--blue)}
.toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%) translateY(100px);background:var(--surface);color:var(--text);padding:12px 24px;border-radius:30px;box-shadow:var(--shadow);transition:.3s;z-index:2000;border:1px solid var(--border)}
.toast.show{transform:translateX(-50%) translateY(0)}

/* Alert Animation */
@keyframes flashAlert {
  0%, 100% { background: var(--surface); }
  50% { background: rgba(239, 68, 68, 0.1); }
}
.alert-item.new-alert { animation: flashAlert 2s 3; }
"""
content = re.sub(r'<style>.*?</style>', f'<style>\n{new_css}\n</style>', content, flags=re.DOTALL)

# 2. Fix the HTML Header/Nav missing elements
# Let's clean up any broken <nav> or <div class="header"> left over.
# Strip all <nav class="nav"> completely to avoid duplicates
content = re.sub(r'<nav class="nav">.*?</nav>', '', content, flags=re.DOTALL)
content = re.sub(r'<div class="header">.*?</div>', '', content, flags=re.DOTALL)
content = re.sub(r'<div class="top-banner">.*?</div>', '', content, flags=re.DOTALL)

# Re-inject the pristine Anjaneya header into the .app
new_header_html = """  <div class="top-banner">🚚 AI Crop Diagnostics | Fast &amp; Accurate Results Within Seconds</div>
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
content = content.replace('<div class="app" id="app">', '<div class="app" id="app">\n' + new_header_html)

# 3. Fix the welcome banner
old_welcome = r'<div class="welcome-banner">.*?</div>'
new_welcome = """<div class="welcome-banner">
        <p style="color:var(--green-d); font-size:14px; font-weight:700; text-transform:uppercase; margin-bottom:16px;">Your Trusted AI Agronomist</p>
        <h2 id="dash-username">Fast &amp; Accurate<br/><span>Crop Analysis</span> Near You</h2>
        <p style="margin-top:16px;">Upload a leaf photo and get an expert diagnostic within seconds.</p>
        <div style="margin-top:32px; display:flex; gap:16px;">
          <button class="btn btn-primary" onclick="switchTab('scan')" style="width:auto; padding:16px 32px;"><span style="font-size:20px;">📷</span> Start AI Scan</button>
          <button class="btn btn-outline" onclick="switchTab('reports')" style="width:auto; padding:16px 32px; border-color:var(--green-d); color:var(--green-d);">View Reports</button>
        </div>
      </div>"""
# only replace the first occurrence (inside dashboard)
content = re.sub(old_welcome, new_welcome, content, count=1, flags=re.DOTALL)

# Make sure enterApp is called automatically
if 'setTimeout(enterApp, 100);' not in content:
    content = content.replace('let currentUser = null;', 'let currentUser = { username: "Admin", id: "dev" };\nsetTimeout(enterApp, 100);')

with open("web/index.html", "w") as f:
    f.write(content)

print("UI fixed successfully.")
