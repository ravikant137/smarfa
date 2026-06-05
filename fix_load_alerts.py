import re

with open("web/index.html", "r") as f:
    content = f.read()

old_alerts_match = re.search(r'// ── Alerts ──────────────────────────────────\nasync function loadAlerts\(\) \{.*?\n\}\n', content, re.DOTALL)

new_alerts = """// ── Alerts ──────────────────────────────────
async function loadAlerts() {
  var el = document.getElementById('alerts-list');
  el.innerHTML = '<div class="loading-overlay"><div class="spinner"></div><p>Loading alerts...</p></div>';
  
  setTimeout(function() {
    var history = JSON.parse(localStorage.getItem('scanHistory') || '[]');
    
    // Filter only warning and critical scans
    var severeScans = history.filter(function(x) { 
        return x.severity === 'critical' || x.severity === 'warning'; 
    });

    if (severeScans.length === 0) {
      el.innerHTML = '<div class="empty-state"><div class="icon">🔔</div><p>No alerts yet — your farm is looking good!</p></div>';
      return;
    }

    var html = severeScans.map(function(s) {
      var cropName = (s.structured && s.structured.final_crop) ? s.structured.final_crop : (s.crop_detected || 'Unknown');
      var typeStr = (s.severity || '').toUpperCase() + ' SCAN: ' + cropName;
      var msg = s.health_assessment || 'Severe crop issue detected';
      var col = s.severity === 'critical' ? 'var(--red)' : 'var(--yellow)';
      var ico = s.severity === 'critical' ? '🚨' : '⚠️';
      var time = new Date(s.timestamp).toLocaleString();
      
      return '<div class="alert-item" style="border-left-color:' + col + '; padding: 12px; margin-bottom: 12px; background: rgba(255,255,255,0.02); border-radius: 8px;">' +
        '<div style="display:flex; align-items:center; justify-content:space-between; margin-bottom: 8px;">' +
        '<span style="font-size:12px; color:var(--muted);">' + ico + ' ' + time + '</span>' +
        '<span style="background:rgba(245,158,11,0.1); color:' + col + '; padding: 2px 8px; border-radius: 4px; font-size:10px; font-weight:700;">AI ALERT</span>' +
        '</div>' +
        '<div style="font-weight:600; font-size:14px; margin-bottom: 4px; color:var(--text);">' + esc(typeStr) + '</div>' +
        '<div style="font-size:13px; color:var(--muted); line-height: 1.5;">' + esc(msg) + '</div>' +
        '</div>';
    }).join('');

    el.innerHTML = html;
  }, 300);
}
"""

if old_alerts_match:
    content = content.replace(old_alerts_match.group(0), new_alerts)
    with open("web/index.html", "w") as f:
        f.write(content)
    print("Replaced loadAlerts successfully")
else:
    print("Could not match old loadAlerts")
