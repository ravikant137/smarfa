import re

with open("web/index.html", "r") as f:
    content = f.read()

# 1. Strip the incorrectly placed footer
content = re.sub(r'<footer class="footer".*?</footer>', '', content, flags=re.DOTALL)

# 2. Add the footer right before the <script> block at the end of the file
footer_html = """
  <footer class="footer" style="background:var(--blue); color:var(--white); padding:60px 48px 24px; margin-top:auto;">
    <div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:40px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:40px; margin-bottom:24px;">
      <div style="flex:1; min-width:250px;">
        <h3 style="font-size:24px; font-weight:800; margin-bottom:16px;">🌱 SMARFA <span style="color:var(--green-l); font-size:12px; text-transform:uppercase;">Diagnostics</span></h3>
        <p style="color:#cbd5e1; font-size:14px; line-height:1.6; max-width:300px;">Providing fast & accurate AI crop diagnostics to empower farmers worldwide. Your trusted AI agronomist.</p>
      </div>
      <div style="flex:1; min-width:200px;">
        <h4 style="font-size:16px; font-weight:700; margin-bottom:16px; color:var(--green-l);">Quick Links</h4>
        <ul style="list-style:none; padding:0; display:flex; flex-direction:column; gap:12px; font-size:14px; color:#cbd5e1;">
          <li><a href="#" onclick="switchTab('dashboard')" style="color:inherit;">Home</a></li>
          <li><a href="#" onclick="switchTab('scan')" style="color:inherit;">AI Scanner</a></li>
          <li><a href="#" onclick="switchTab('reports')" style="color:inherit;">Lab Reports</a></li>
        </ul>
      </div>
      <div style="flex:1; min-width:200px;">
        <h4 style="font-size:16px; font-weight:700; margin-bottom:16px; color:var(--green-l);">Contact Us</h4>
        <ul style="list-style:none; padding:0; display:flex; flex-direction:column; gap:12px; font-size:14px; color:#cbd5e1;">
          <li>📞 +1 (800) 123-4567</li>
          <li>✉️ support@smarfa.ai</li>
          <li>📍 Global Farming Hub</li>
        </ul>
      </div>
    </div>
    <div style="text-align:center; color:#94a3b8; font-size:12px;">
      &copy; 2026 Smarfa Diagnostics. All rights reserved.
    </div>
  </footer>
"""

# Find the last <script> block and insert right before it
content = re.sub(r'(\n<script>)', footer_html + r'\1', content, count=1)

with open("web/index.html", "w") as f:
    f.write(content)

print("Footer injected successfully.")
