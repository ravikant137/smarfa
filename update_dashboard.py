import re

with open("web/index.html", "r") as f:
    content = f.read()

# 1. Update the color palette to farmer-friendly warm earthy tones
old_root = """:root{
  --bg:#f5f7fa;--surface:#ffffff;--card:#f8fafc;--border:#e2e8f0;
  --green:#4CAF50;--green-l:#81c784;--green-d:#2e7d32;
  --yellow:#f59e0b;--red:#ef4444;--blue:#003366;--purple:#8b5cf6;--cyan:#06b6d4;
  --text:#1a1a2e;--muted:#64748b;--white:#fff;
  --radius:14px;--radius-sm:10px;
  --shadow:0 4px 24px rgba(0,0,0,.08);
}"""
new_root = """:root{
  --bg:#faf7f2;--surface:#ffffff;--card:#f5f0e8;--border:#d6cdc0;
  --green:#3d7a3a;--green-l:#6ab04c;--green-d:#2a5c28;
  --yellow:#d4952a;--red:#c0392b;--blue:#2c4a1e;--purple:#6b4226;--cyan:#1a6b3a;
  --text:#2c2c1a;--muted:#7a6a52;--white:#fff;
  --radius:14px;--radius-sm:10px;
  --shadow:0 4px 24px rgba(0,0,0,.10);
  --soil:#8B5E3C;--sky:#5ba4cf;--harvest:#e8a838;
}"""
content = content.replace(old_root, new_root)

# 2. Upgrade body background
content = content.replace(
  "body{font-family:'Inter','Segoe UI',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;overflow-x:hidden}",
  "body{font-family:'Inter','Segoe UI',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;overflow-x:hidden;background-image:url(\"data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%234CAF50' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E\");}"
)

# 3. Replace the welcome banner content with the map-based dashboard
old_dashboard = """    <div class="tab active" id="tab-dashboard">
      <div class="welcome-banner">
        <p style="color:var(--green-d); font-size:14px; font-weight:700; text-transform:uppercase; margin-bottom:16px;">Your Trusted AI Agronomist</p>
        <h2 id="dash-username">Fast &amp; Accurate<br/><span>Crop Analysis</span> Near You</h2>
        <p style="margin-top:16px;">Upload a leaf photo and get an expert diagnostic within seconds.</p>
        <div style="margin-top:32px; display:flex; gap:16px;">
          <button class="btn btn-primary" onclick="switchTab('scan')" style="width:auto; padding:16px 32px;"><span style="font-size:20px;">📷</span> Start AI Scan</button>
          <button class="btn btn-outline" onclick="switchTab('reports')" style="width:auto; padding:16px 32px; border-color:var(--green-d); color:var(--green-d);">View Reports</button>
        </div>
      </div>

      <div id="health-score-wrap" style="text-align:center;margin-bottom:16px">
        <div class="health-ring" id="health-ring" style="background:conic-gradient(#10B981 0deg, #10B981 0deg, #334155 0deg)">
          <span class="score" id="health-score">—</span>
        </div>
        <div style="font-size:12px;color:var(--muted);margin-top:8px">Farm Health Score</div>
      </div>

      <div class="stat-grid" id="dash-stats">
        <div class="stat-card"><div class="icon">🌡️</div><div class="label">Temperature</div><div class="value" id="s-temp">—</div><div class="sub" id="s-temp-sub"></div></div>
        <div class="stat-card"><div class="icon">💧</div><div class="label">Soil Moisture</div><div class="value" id="s-moisture">—</div><div class="sub" id="s-moisture-sub"></div></div>
        <div class="stat-card"><div class="icon">📏</div><div class="label">Avg Height</div><div class="value" id="s-height">—</div><div class="sub" id="s-height-sub"></div></div>
        <div class="stat-card"><div class="icon">🚨</div><div class="label">Alerts (7d)</div><div class="value" id="s-alerts">—</div><div class="sub" id="s-alerts-sub"></div></div>
      </div>

      <!-- Water Pump Status -->
      <div class="section-title">💧 Water Pump Control</div>
      <div class="pump-card" id="pump-card">
        <div class="pump-status">
          <div class="pump-indicator off" id="pump-indicator"></div>
          <div>
            <div id="pump-status-text" style="font-weight:600;font-size:14px">Pump Offline</div>
            <div id="pump-status-detail" style="font-size:12px;color:var(--muted)">No active irrigation</div>
          </div>
        </div>
        <div class="pump-btns">
          <button class="btn btn-primary btn-sm" onclick="startPump()">💧 Start Pump</button>
          <button class="btn btn-danger btn-sm" onclick="stopPump()">⏹ Stop Pump</button>
        </div>
        <div class="pump-log" id="pump-log"></div>
      </div>

    </div>"""

new_dashboard = """    <div class="tab active" id="tab-dashboard">

      <!-- Hero Banner -->
      <div class="welcome-banner" style="background:linear-gradient(135deg, #2a5c28 0%, #3d7a3a 50%, #6ab04c 100%); color:#fff; position:relative; overflow:hidden; padding:48px; margin-bottom:24px; border-radius:20px; border:none; box-shadow:0 12px 40px rgba(42,92,40,0.3);">
        <div style="position:absolute;top:-60px;right:-60px;width:240px;height:240px;background:rgba(255,255,255,0.06);border-radius:50%;"></div>
        <div style="position:absolute;bottom:-40px;right:80px;width:160px;height:160px;background:rgba(255,255,255,0.04);border-radius:50%;"></div>
        <p style="color:rgba(255,255,255,0.8); font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:2px; margin-bottom:12px;">🌾 Smarfa AI Farm Intelligence</p>
        <h2 style="font-size:38px;font-weight:900;color:#fff;line-height:1.15;margin-bottom:12px;" id="dash-username">Your <span style="color:#a8e063;">Smart Farm</span><br/>Command Centre</h2>
        <p style="color:rgba(255,255,255,0.75); font-size:16px; margin-bottom:28px;">Scan crops. Track fields. Protect your harvest — all in one place.</p>
        <div style="display:flex;gap:14px;flex-wrap:wrap;">
          <button onclick="switchTab('scan')" style="background:#fff;color:#2a5c28;border:none;padding:14px 28px;font-size:14px;font-weight:800;border-radius:50px;cursor:pointer;display:flex;align-items:center;gap:8px;transition:.2s;box-shadow:0 4px 14px rgba(0,0,0,0.2);">📷 Start AI Scan</button>
          <button onclick="switchTab('reports')" style="background:rgba(255,255,255,0.15);color:#fff;border:2px solid rgba(255,255,255,0.4);padding:14px 28px;font-size:14px;font-weight:700;border-radius:50px;cursor:pointer;display:flex;align-items:center;gap:8px;transition:.2s;backdrop-filter:blur(4px);">📊 View Reports</button>
        </div>
      </div>

      <!-- Weather & Stats Row -->
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:24px;" id="dash-stats">
        <div style="background:#fff;border-radius:16px;padding:18px;border:1px solid var(--border);box-shadow:0 2px 12px rgba(0,0,0,0.05);text-align:center;cursor:default;transition:.2s;" onmouseover="this.style.transform='translateY(-3px)'" onmouseout="this.style.transform='none'">
          <div style="font-size:32px;margin-bottom:8px;">🌡️</div>
          <div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px;">Temperature</div>
          <div style="font-size:22px;font-weight:800;color:var(--text)" id="s-temp">—</div>
          <div style="font-size:11px;color:var(--muted);margin-top:2px" id="s-temp-sub">Loading...</div>
        </div>
        <div style="background:#fff;border-radius:16px;padding:18px;border:1px solid var(--border);box-shadow:0 2px 12px rgba(0,0,0,0.05);text-align:center;transition:.2s;" onmouseover="this.style.transform='translateY(-3px)'" onmouseout="this.style.transform='none'">
          <div style="font-size:32px;margin-bottom:8px;">💧</div>
          <div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px;">Soil Moisture</div>
          <div style="font-size:22px;font-weight:800;color:var(--sky)" id="s-moisture">—</div>
          <div style="font-size:11px;color:var(--muted);margin-top:2px" id="s-moisture-sub">Loading...</div>
        </div>
        <div style="background:#fff;border-radius:16px;padding:18px;border:1px solid var(--border);box-shadow:0 2px 12px rgba(0,0,0,0.05);text-align:center;transition:.2s;" onmouseover="this.style.transform='translateY(-3px)'" onmouseout="this.style.transform='none'">
          <div style="font-size:32px;margin-bottom:8px;">📏</div>
          <div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px;">Avg Height</div>
          <div style="font-size:22px;font-weight:800;color:var(--green)" id="s-height">—</div>
          <div style="font-size:11px;color:var(--muted);margin-top:2px" id="s-height-sub">Loading...</div>
        </div>
        <div style="background:#fff;border-radius:16px;padding:18px;border:1px solid var(--border);box-shadow:0 2px 12px rgba(0,0,0,0.05);text-align:center;transition:.2s;" onmouseover="this.style.transform='translateY(-3px)'" onmouseout="this.style.transform='none'">
          <div style="font-size:32px;margin-bottom:8px;">🚨</div>
          <div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px;">Alerts (7d)</div>
          <div style="font-size:22px;font-weight:800;color:var(--red)" id="s-alerts">—</div>
          <div style="font-size:11px;color:var(--muted);margin-top:2px" id="s-alerts-sub">Loading...</div>
        </div>
      </div>

      <!-- Main Row: Map + Sidebar -->
      <div style="display:grid;grid-template-columns:1fr 340px;gap:20px;margin-bottom:24px;">
        
        <!-- Field Map Card -->
        <div style="background:#fff;border-radius:20px;border:1px solid var(--border);box-shadow:0 4px 20px rgba(0,0,0,0.06);overflow:hidden;">
          <div style="padding:18px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;">
            <div>
              <div style="font-size:16px;font-weight:800;color:var(--text);">🗺️ My Farm Fields</div>
              <div style="font-size:12px;color:var(--muted);margin-top:2px;">Click a field marker to view details</div>
            </div>
            <button onclick="addField()" style="background:var(--green);color:#fff;border:none;padding:8px 16px;border-radius:50px;font-size:12px;font-weight:700;cursor:pointer;">+ Add Field</button>
          </div>
          <div id="farm-map" style="height:420px;background:linear-gradient(135deg,#2d5a1b 0%,#3d7a3a 30%,#4a9e3f 50%,#6ab04c 70%,#3d7a3a 100%);position:relative;overflow:hidden;">
            <!-- Satellite-style background grid -->
            <svg width="100%" height="100%" style="position:absolute;top:0;left:0;opacity:0.15;">
              <defs><pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M 40 0 L 0 0 0 40" fill="none" stroke="#fff" stroke-width="0.5"/></pattern></defs>
              <rect width="100%" height="100%" fill="url(#grid)"/>
            </svg>
            <!-- Simulated field plots -->
            <svg width="100%" height="100%" viewBox="0 0 800 420" style="position:absolute;top:0;left:0;">
              <!-- Field A -->
              <polygon points="100,60 260,40 300,160 120,180" fill="rgba(106,176,76,0.6)" stroke="#fff" stroke-width="2" style="cursor:pointer;" onclick="selectField('A')" id="field-svg-A"/>
              <!-- Field B -->
              <polygon points="310,50 480,30 500,150 330,170" fill="rgba(91,164,207,0.5)" stroke="#fff" stroke-width="2" style="cursor:pointer;" onclick="selectField('B')" id="field-svg-B"/>
              <!-- Field C -->
              <polygon points="120,200 300,185 310,320 130,340" fill="rgba(232,168,56,0.55)" stroke="#fff" stroke-width="2" style="cursor:pointer;" onclick="selectField('C')" id="field-svg-C"/>
              <!-- Field D -->
              <polygon points="320,180 490,160 510,290 340,310" fill="rgba(106,176,76,0.5)" stroke="#fff" stroke-width="2" style="cursor:pointer;" onclick="selectField('D')" id="field-svg-D"/>
              <!-- Field E -->
              <polygon points="520,40 680,30 700,160 540,170" fill="rgba(192,57,43,0.4)" stroke="#fff" stroke-width="2" style="cursor:pointer;" onclick="selectField('E')" id="field-svg-E"/>
              <!-- Labels -->
              <text x="185" y="115" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle" style="pointer-events:none;">A</text>
              <text x="405" y="100" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle" style="pointer-events:none;">B</text>
              <text x="215" y="265" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle" style="pointer-events:none;">C</text>
              <text x="415" y="240" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle" style="pointer-events:none;">D</text>
              <text x="610" y="100" fill="#fff" font-size="14" font-weight="bold" text-anchor="middle" style="pointer-events:none;">E</text>
              <!-- Field E warning icon -->
              <text x="610" y="80" fill="#ff6b6b" font-size="18" text-anchor="middle" style="pointer-events:none;">⚠</text>
            </svg>
            <!-- Map Legend -->
            <div style="position:absolute;bottom:16px;left:16px;background:rgba(0,0,0,0.5);backdrop-filter:blur(6px);border-radius:10px;padding:10px 14px;color:#fff;font-size:11px;">
              <div style="margin-bottom:4px;font-weight:700;">LEGEND</div>
              <div style="display:flex;align-items:center;gap:6px;margin-bottom:3px;"><div style="width:12px;height:12px;background:rgba(106,176,76,0.8);border-radius:2px;"></div> Healthy</div>
              <div style="display:flex;align-items:center;gap:6px;margin-bottom:3px;"><div style="width:12px;height:12px;background:rgba(91,164,207,0.8);border-radius:2px;"></div> Irrigating</div>
              <div style="display:flex;align-items:center;gap:6px;margin-bottom:3px;"><div style="width:12px;height:12px;background:rgba(232,168,56,0.8);border-radius:2px;"></div> Harvesting</div>
              <div style="display:flex;align-items:center;gap:6px;"><div style="width:12px;height:12px;background:rgba(192,57,43,0.7);border-radius:2px;"></div> Alert</div>
            </div>
            <!-- Scale bar -->
            <div style="position:absolute;bottom:16px;right:16px;background:rgba(0,0,0,0.5);backdrop-filter:blur(6px);border-radius:8px;padding:8px 12px;color:#fff;font-size:10px;">
              <div style="border-bottom:2px solid #fff;width:60px;margin-bottom:4px;"></div>
              <div>500m</div>
            </div>
          </div>
          <!-- Field detail popup -->
          <div id="field-detail" style="padding:16px 20px;border-top:1px solid var(--border);display:none;">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
              <div style="font-weight:700;font-size:15px;" id="field-detail-name">Field A</div>
              <div id="field-detail-status" style="font-size:11px;font-weight:700;padding:4px 10px;border-radius:50px;background:rgba(61,122,58,0.1);color:var(--green)">🟢 HEALTHY</div>
            </div>
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;">
              <div style="text-align:center;padding:10px;background:var(--card);border-radius:10px;">
                <div style="font-size:18px;margin-bottom:4px;" id="field-detail-icon">🌾</div>
                <div style="font-size:10px;color:var(--muted);margin-bottom:2px;">CROP</div>
                <div style="font-size:13px;font-weight:700;" id="field-detail-crop">Wheat</div>
              </div>
              <div style="text-align:center;padding:10px;background:var(--card);border-radius:10px;">
                <div style="font-size:18px;margin-bottom:4px;">📐</div>
                <div style="font-size:10px;color:var(--muted);margin-bottom:2px;">AREA</div>
                <div style="font-size:13px;font-weight:700;" id="field-detail-area">4.2 acres</div>
              </div>
              <div style="text-align:center;padding:10px;background:var(--card);border-radius:10px;">
                <div style="font-size:18px;margin-bottom:4px;">📅</div>
                <div style="font-size:10px;color:var(--muted);margin-bottom:2px;">PLANTED</div>
                <div style="font-size:13px;font-weight:700;" id="field-detail-planted">Jan 12</div>
              </div>
            </div>
            <button onclick="switchTab('scan')" style="width:100%;background:var(--green);color:#fff;border:none;padding:10px;border-radius:10px;font-size:13px;font-weight:700;cursor:pointer;margin-top:12px;display:flex;align-items:center;justify-content:center;gap:6px;">📷 Scan This Field Now</button>
          </div>
        </div>

        <!-- Right Sidebar: Field List + Pump -->
        <div style="display:flex;flex-direction:column;gap:16px;">
          <!-- Health Score Ring -->
          <div style="background:#fff;border-radius:16px;padding:20px;border:1px solid var(--border);box-shadow:0 2px 12px rgba(0,0,0,0.05);text-align:center;">
            <div style="font-size:13px;font-weight:700;color:var(--text);margin-bottom:14px;">🌿 Farm Health Score</div>
            <div class="health-ring" id="health-ring" style="background:conic-gradient(#3d7a3a 0deg, #3d7a3a 0deg, #e2e8f0 0deg); width:100px;height:100px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 10px;position:relative;">
              <div style="background:#fff;width:76px;height:76px;border-radius:50%;display:flex;align-items:center;justify-content:center;position:absolute;">
                <span class="score" id="health-score" style="font-size:26px;font-weight:900;color:var(--green-d);">—</span>
              </div>
            </div>
            <div style="font-size:12px;color:var(--muted);" id="health-score-label">Calculating...</div>
          </div>

          <!-- Field Region List -->
          <div style="background:#fff;border-radius:16px;border:1px solid var(--border);box-shadow:0 2px 12px rgba(0,0,0,0.05);overflow:hidden;flex:1;">
            <div style="padding:14px 16px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;">
              <div style="font-weight:700;font-size:14px;">📋 Region List</div>
              <div style="font-size:11px;color:var(--muted);">5 fields</div>
            </div>
            <div id="region-list" style="overflow-y:auto;max-height:340px;">
              <!-- Generated by JS -->
            </div>
          </div>

          <!-- Pump Control -->
          <div class="pump-card" id="pump-card" style="background:#fff;border-radius:16px;padding:16px;border:1px solid var(--border);box-shadow:0 2px 12px rgba(0,0,0,0.05);">
            <div style="font-weight:700;font-size:13px;margin-bottom:12px;">💧 Irrigation Control</div>
            <div class="pump-status" style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
              <div class="pump-indicator off" id="pump-indicator" style="width:12px;height:12px;border-radius:50%;background:var(--muted);"></div>
              <div>
                <div id="pump-status-text" style="font-weight:600;font-size:13px">Pump Offline</div>
                <div id="pump-status-detail" style="font-size:11px;color:var(--muted)">No active irrigation</div>
              </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
              <button class="btn btn-primary btn-sm" onclick="startPump()" style="background:var(--sky);border-radius:10px;font-size:12px;">💧 Start</button>
              <button class="btn btn-sm" onclick="stopPump()" style="background:rgba(192,57,43,0.1);color:var(--red);border:1px solid rgba(192,57,43,0.3);border-radius:10px;font-size:12px;">⏹ Stop</button>
            </div>
            <div class="pump-log" id="pump-log"></div>
          </div>
        </div>
      </div>

      <!-- Recent Scan Activity Strip -->
      <div style="background:#fff;border-radius:16px;padding:20px;border:1px solid var(--border);box-shadow:0 2px 12px rgba(0,0,0,0.05);">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
          <div style="font-weight:800;font-size:15px;">🔬 Recent AI Scan Activity</div>
          <button onclick="switchTab('reports')" style="background:none;border:1px solid var(--border);padding:6px 14px;border-radius:50px;font-size:12px;font-weight:600;cursor:pointer;color:var(--muted);">View All →</button>
        </div>
        <div id="dash-recent-scans" style="display:flex;flex-direction:column;gap:10px;">
          <div style="text-align:center;padding:20px;color:var(--muted);font-size:13px;">No scans yet. <a href="#" onclick="switchTab('scan');return false;" style="color:var(--green);font-weight:700;">Start your first scan →</a></div>
        </div>
      </div>

    </div>"""

content = content.replace(old_dashboard, new_dashboard)

with open("web/index.html", "w") as f:
    f.write(content)

print("Dashboard replaced")
