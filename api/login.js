import { supabase } from './utils/supabase.js';

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ detail: 'Method Not Allowed' });

  const { username, password } = req.body || {};

  try {
    if (!supabase) {
      return res.status(500).json({ detail: 'Backend login failed: Supabase credentials are not configured on Vercel' });
    }

    const { data, error } = await supabase.auth.signInWithPassword({
      email: username,
      password,
    });

    if (error) {
      return res.status(400).json({ detail: error.message || 'Invalid credentials' });
    }

    return res.status(200).json({
      status: 'login successful',
      user_id: data.user.id,
      username: username
    });
  } catch (error) {
    return res.status(500).json({ detail: 'Backend login failed' });
  }
}
