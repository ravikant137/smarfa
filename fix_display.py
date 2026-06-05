import re

with open("web/index.html", "r") as f:
    content = f.read()

# 1. Fix the display=block issue in analyzeCrop
old_success = """    d.timestamp = new Date().toISOString();
    history.push(d);
    localStorage.setItem('scanHistory', JSON.stringify(history));
  } catch(e) {"""

new_success = """    d.timestamp = new Date().toISOString();
    history.push(d);
    localStorage.setItem('scanHistory', JSON.stringify(history));
    results.style.display = 'block';
  } catch(e) {"""

content = content.replace(old_success, new_success)

# 2. Fix loadAlerts() to include warnings/critical scans from history
old_alerts = """async function loadAlerts() {
  var list = document.getElementById('alerts-list');
  list.innerHTML = '<div class="loading-overlay"><div class="spinner"></div><p>Loading alerts...</p></div>';
  try {
    var r = await fetch('/api/v1/sensors/alerts', {
      headers: { 'Authorization': 'Bearer ' + (currentUser ? currentUser.token : '') }
    });
    if (!r.ok) throw new Error('Network error');
    var d = await r.json();"""

new_alerts = """async function loadAlerts() {
  var list = document.getElementById('alerts-list');
  list.innerHTML = '<div class="loading-overlay"><div class="spinner"></div><p>Loading alerts...</p></div>';
  try {
    // Dynamically pull critical/warning alerts from local scan history
    var history = JSON.parse(localStorage.getItem('scanHistory') || '[]');
    var severeScans = history.filter(x => x.severity === 'critical' || x.severity === 'warning');
    
    var d = { alerts: severeScans.map(s => ({
       id: Math.random(),
       type: s.severity.toUpperCase() + ' SCAN',
       message: s.health_assessment || 'Severe crop issue detected',
       timestamp: s.timestamp
    })) };"""

content = content.replace(old_alerts, new_alerts)

with open("web/index.html", "w") as f:
    f.write(content)

print("Fixed display block and alerts")
