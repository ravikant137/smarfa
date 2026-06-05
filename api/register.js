import { supabase } from './utils/supabase.js';

export default async function handler(req, res) {
  // Handle CORS Preflight
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'X-Requested-With, Content-Type, Accept, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') return res.status(405).json({ detail: 'Method Not Allowed' });

  const { username, password } = req.body || {};

  try {
    if (!supabase) {
      return res.status(500).json({ detail: 'Backend registration failed: Supabase credentials are not configured on Vercel' });
    }

    const { data, error } = await supabase.auth.signUp({
      email: username,
      password,
    });

    if (error) {
      return res.status(400).json({ detail: error.message || 'Registration failed' });
    }

    return res.status(200).json({
      status: 'user registered',
      id: data.user.id,
      username: username
    });
  } catch (error) {
    return res.status(500).json({ detail: 'Backend registration failed' });
  }
}
