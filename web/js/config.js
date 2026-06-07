// web/js/config.js — Global constants and shared state

window.APP = {
  API: (window.location.origin && !window.location.origin.startsWith('file://'))
    ? window.location.origin
    : 'http://192.168.29.181:8000',
  AGRO_API_KEY: '8518d290ab4e6f4ca86ee6c7d841b3fb',
  userLat: null,
  userLon: null,
};

// Shared toast notification
window.toast = function(msg, type = 'success') {
  var t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.style.background = type === 'error' ? '#ef4444' : type === 'warning' ? '#f59e0b' : '#3d7a3a';
  t.className = 'toast show';
  setTimeout(() => t.classList.remove('show'), 4000);
};
