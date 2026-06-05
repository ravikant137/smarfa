import re

with open("web/index.html", "r") as f:
    content = f.read()

# I need to add toast notification inside analyzeCrop() right after setting history
old_success = """    localStorage.setItem('scanHistory', JSON.stringify(history));
    results.style.display = 'block';
  } catch(e) {"""

new_success = """    localStorage.setItem('scanHistory', JSON.stringify(history));
    results.style.display = 'block';
    
    // Trigger Push Notification/Alert
    var sev = d.severity || 'warning';
    if (sev === 'critical') {
       toast('🚨 CRITICAL ALERT: ' + (d.health_assessment || 'Severe issue detected!'), 'error');
    } else if (sev === 'warning') {
       toast('⚠️ WARNING: ' + (d.health_assessment || 'Potential issue detected.'), 'warning');
    } else {
       toast('✅ Scan Complete: Crop is healthy!');
    }
  } catch(e) {"""

content = content.replace(old_success, new_success)

# Let's also make sure loadAlerts handles the severity colors properly
old_alerts = """var d = { alerts: severeScans.map(s => ({
       id: Math.random(),
       type: s.severity.toUpperCase() + ' SCAN',
       message: s.health_assessment || 'Severe crop issue detected',
       timestamp: s.timestamp
    })) };"""

new_alerts = """var d = { alerts: severeScans.map(s => ({
       id: Math.random(),
       type: s.severity.toUpperCase() + ' SCAN: ' + (s.structured && s.structured.final_crop ? s.structured.final_crop : s.crop_detected || 'Unknown'),
       message: s.health_assessment || 'Severe crop issue detected',
       timestamp: s.timestamp
    })) };"""

content = content.replace(old_alerts, new_alerts)

with open("web/index.html", "w") as f:
    f.write(content)

print("Added notifications to analyzeCrop")
