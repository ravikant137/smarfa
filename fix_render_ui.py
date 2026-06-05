import re

with open("web/index.html", "r") as f:
    content = f.read()

# I need to replace the entire renderResults function
old_render_match = re.search(r'function renderResults\(d\).*?\n\}', content, re.DOTALL)

if old_render_match:
    new_render = """function renderResults(d) {
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
}"""
    content = content.replace(old_render_match.group(0), new_render)
    
    with open("web/index.html", "w") as f:
        f.write(content)
    print("Updated renderResults to match design")
else:
    print("Could not find renderResults block")
