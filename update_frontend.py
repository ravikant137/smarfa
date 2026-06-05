import re

with open("web/index.html", "r") as f:
    content = f.read()

# 1. Update analyzeCrop() to inject location
old_analyze = """    var payload = { 
      image_base64: imageBase64,
      crop_hint: hintVal !== 'auto' ? hintVal : null
    };"""

new_analyze = """    var payload = { 
      image_base64: imageBase64,
      crop_hint: hintVal !== 'auto' ? hintVal : null,
      lat: window.userLat || 0,
      lon: window.userLon || 0
    };"""

content = content.replace(old_analyze, new_analyze)

# Add geolocation fetch on page load
geo_script = """
if ("geolocation" in navigator) {
  navigator.geolocation.getCurrentPosition(function(position) {
    window.userLat = position.coords.latitude;
    window.userLon = position.coords.longitude;
  });
}
"""
content = content.replace("let currentUser = {", geo_script + "\nlet currentUser = {")

# 2. Add Community Expert button to the scan results
old_scan_btn = """      </div>
    </div>

    <!-- ── Tab: Farm Reports ───────── -->"""

new_scan_btn = """      </div>
      
      <!-- Community Forum / Expert Fallback (Plantix style) -->
      <div id="expert-fallback" style="display:none; margin-top:24px; padding:20px; background:#eef2ff; border:1px solid #c7d2fe; border-radius:14px; text-align:center;">
        <h3 style="color:#3730a3; font-size:18px; margin-bottom:8px;">Not sure about the AI result?</h3>
        <p style="color:#4f46e5; font-size:14px; margin-bottom:16px;">Share your scan with our community of agronomists and local farmers for expert verification.</p>
        <button class="btn btn-primary" style="width:auto; margin:0 auto; padding:12px 24px; background:#4f46e5;">Ask Community Experts</button>
      </div>

    </div>

    <!-- ── Tab: Farm Reports ───────── -->"""

content = content.replace(old_scan_btn, new_scan_btn)

# Make the expert fallback visible when results are rendered
content = content.replace("document.getElementById('scan-results').innerHTML = cropIdHtml + diseaseHtml;", "document.getElementById('scan-results').innerHTML = cropIdHtml + diseaseHtml;\n  document.getElementById('expert-fallback').style.display = 'block';")

with open("web/index.html", "w") as f:
    f.write(content)

print("Updated index.html frontend")
