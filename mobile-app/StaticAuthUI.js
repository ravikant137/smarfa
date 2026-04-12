import React, { useState } from 'react';

export default function StaticAuthUI() {
  const [tab, setTab] = useState('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Center the card using a wrapper div
  const wrapperStyle = {
    minHeight: '100vh',
    width: '100vw',
    background: '#0F172A',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'fixed',
    left: 0,
    top: 0,
    zIndex: 1,
  };

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    if (!username || !password || (tab === 'register' && !confirm)) {
      setError('Please fill in all fields');
      return;
    }
    if (tab === 'register' && password !== confirm) {
      setError('Passwords do not match');
      return;
    }
    setLoading(true);
    try {
      const API = 'http://localhost:8001'; // Update this if your backend runs elsewhere
      const endpoint = tab === 'register' ? '/register' : '/login';
      const res = await fetch(API + endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Authentication failed');
      // Success: reload or redirect as needed
      window.location.reload();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={wrapperStyle}>
      <div style={{ width: 400, background: '#1E2333', borderRadius: 18, padding: 36, boxShadow: '0 8px 32px #0008' }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ fontSize: 56, marginBottom: 8 }}>🌱</div>
          <h1 style={{ fontSize: 36, fontWeight: 800, color: '#22D3AE', letterSpacing: 1 }}>Smarfa</h1>
          <p style={{ color: '#94A3B8', marginTop: 6, fontSize: 15 }}>Smart AI Farming — Protect & Grow Your Crops</p>
        </div>
        <div style={{ display: 'flex', background: '#23273a', borderRadius: 12, marginBottom: 24 }}>
          <button onClick={() => setTab('login')} style={{ flex: 1, padding: 12, border: 'none', borderRadius: 10, fontWeight: 600, fontSize: 15, background: tab === 'login' ? '#223' : 'transparent', color: tab === 'login' ? '#fff' : '#94A3B8', cursor: 'pointer', transition: '.2s' }}>Sign In</button>
          <button onClick={() => setTab('register')} style={{ flex: 1, padding: 12, border: 'none', borderRadius: 10, fontWeight: 600, fontSize: 15, background: tab === 'register' ? '#10B981' : 'transparent', color: tab === 'register' ? '#fff' : '#94A3B8', cursor: 'pointer', transition: '.2s' }}>Register</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 16 }}>
            <label style={{ color: '#94A3B8', fontSize: 14, fontWeight: 500, marginBottom: 6, display: 'block' }}>Username</label>
            <input value={username} onChange={e => setUsername(e.target.value)} style={{ width: '100%', padding: 14, borderRadius: 10, border: '1.5px solid #334155', background: '#23273a', color: '#fff', fontSize: 16, outline: 'none', marginBottom: 0 }} placeholder="ravi@test.com" />
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={{ color: '#94A3B8', fontSize: 14, fontWeight: 500, marginBottom: 6, display: 'block' }}>Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} style={{ width: '100%', padding: 14, borderRadius: 10, border: '1.5px solid #334155', background: '#23273a', color: '#fff', fontSize: 16, outline: 'none', marginBottom: 0 }} />
          </div>
          {tab === 'register' && (
            <div style={{ marginBottom: 16 }}>
              <label style={{ color: '#94A3B8', fontSize: 14, fontWeight: 500, marginBottom: 6, display: 'block' }}>Confirm Password</label>
              <input type="password" value={confirm} onChange={e => setConfirm(e.target.value)} style={{ width: '100%', padding: 14, borderRadius: 10, border: '1.5px solid #334155', background: '#23273a', color: '#fff', fontSize: 16, outline: 'none', marginBottom: 0 }} />
            </div>
          )}
          <button type="submit" style={{ width: '100%', padding: 16, borderRadius: 10, border: 'none', background: '#10B981', color: '#fff', fontWeight: 700, fontSize: 18, marginTop: 8, marginBottom: 8, cursor: loading ? 'not-allowed' : 'pointer', boxShadow: '0 2px 8px #10B98144', opacity: loading ? 0.7 : 1 }} disabled={loading}>
            {loading ? (tab === 'register' ? 'Creating...' : 'Signing in...') : (tab === 'register' ? 'Create Account' : 'Sign In')}
          </button>
          {error && <div style={{ color: '#EF4444', fontSize: 14, marginTop: 8, textAlign: 'center' }}>{error}</div>}
        </form>
      </div>
    </div>
  );
}
