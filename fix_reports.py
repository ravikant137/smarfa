import re

with open("web/index.html", "r") as f:
    content = f.read()

# 1. Replace the entire tab-reports HTML
old_reports_html_match = re.search(r'<div class="tab" id="tab-reports">.*?</div>\n    </div>\n\n    <!-- ── Tab: Alerts', content, re.DOTALL)

new_reports_html = """<div class="tab" id="tab-reports">
      <div class="section-title">📊 Farm & Crop Insights</div>
      
      <div id="reports-loading" class="loading-overlay" style="display:none">
        <div class="spinner"></div>
        <p>Analyzing historical data...</p>
      </div>

      <div id="reports-content" style="display:none">
        <div class="report-grid" style="display:grid; grid-template-columns: 1fr; gap:16px;">
          <!-- Health Score -->
          <div class="result-card" style="display:flex; justify-content:space-between; align-items:center;">
            <div>
              <h3>Overall Farm Health</h3>
              <p style="color:var(--muted); font-size:13px; margin-top:4px;">Based on your AI scan history</p>
            </div>
            <div class="health-ring" id="report-health-ring" style="background:conic-gradient(#10B981 0deg, #334155 0deg); width:80px; height:80px; border-radius:50%; display:flex; align-items:center; justify-content:center; position:relative;">
              <div style="background:var(--card); width:64px; height:64px; border-radius:50%; display:flex; align-items:center; justify-content:center; position:absolute;">
                <span class="score" id="report-health-score" style="font-size:20px; font-weight:800;">—</span>
              </div>
            </div>
          </div>
          
          <!-- Scan History List -->
          <div class="result-card">
            <h3>📈 Crop Scan History (Start to End)</h3>
            <div id="reports-history-list" style="margin-top:16px; display:flex; flex-direction:column; gap:12px;"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Tab: Alerts"""

if old_reports_html_match:
    content = content.replace(old_reports_html_match.group(0), new_reports_html)
else:
    print("Could not match tab-reports HTML")

# 2. Replace the loadReports() function
old_load_reports_match = re.search(r'async function loadReports\(\) \{.*?\n\}\n', content, re.DOTALL)

new_load_reports = """async function loadReports() {
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
"""

if old_load_reports_match:
    content = content.replace(old_load_reports_match.group(0), new_load_reports)
else:
    print("Could not match loadReports function")

with open("web/index.html", "w") as f:
    f.write(content)

print("Rebuilt Reports UI")
