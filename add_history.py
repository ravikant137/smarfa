import re

with open("web/index.html", "r") as f:
    content = f.read()

# 1. Add localStorage saving inside analyzeCrop()
old_render = "renderResults(d);"
new_render = """renderResults(d);
    // Save to local scan history
    var history = JSON.parse(localStorage.getItem('scanHistory') || '[]');
    d.timestamp = new Date().toISOString();
    history.push(d);
    localStorage.setItem('scanHistory', JSON.stringify(history));"""
content = content.replace(old_render, new_render)

# 2. Update loadReports() to read from localStorage instead of dummy fetch
old_reports = """async function loadReports() {
  var content = document.getElementById('report-content');
  content.innerHTML = '<div class="loading-overlay" style="position:relative;display:flex;min-height:200px"><div class="spinner"></div><p>Generating reports...</p></div>';
  try {
    var r = await fetch('/api/v1/sensors/reports', {
      headers: { 'Authorization': 'Bearer ' + (currentUser ? currentUser.token : '') }
    });
    if (!r.ok) throw new Error('Network error');
    var d = await r.json();"""

new_reports = """async function loadReports() {
  var content = document.getElementById('report-content');
  content.innerHTML = '<div class="loading-overlay" style="position:relative;display:flex;min-height:200px"><div class="spinner"></div><p>Generating reports...</p></div>';
  try {
    // Generate reports dynamically from local scan history!
    var history = JSON.parse(localStorage.getItem('scanHistory') || '[]');
    if (history.length === 0) {
       content.innerHTML = '<div class="empty-state"><div class="icon">📊</div><p>No scans yet. Upload a crop image to generate history.</p></div>';
       return;
    }
    
    var healthy = history.filter(x => x.severity === 'healthy').length;
    var warning = history.filter(x => x.severity === 'warning').length;
    var critical = history.filter(x => x.severity === 'critical').length;
    var score = Math.round((healthy / history.length) * 100) || 0;
    
    var d = {
       health_score: score,
       healthy_crops: healthy,
       at_risk_crops: warning,
       critical_crops: critical,
       recent_scans: history.slice(-5).reverse()
    };
"""
content = content.replace(old_reports, new_reports)

with open("web/index.html", "w") as f:
    f.write(content)

print("Added history logic")
