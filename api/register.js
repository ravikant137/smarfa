export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ detail: 'Method Not Allowed' });

  const { username, password } = req.body || {};
  const supabaseUrl = process.env.SUPABASE_URL;
  const anonKey = process.env.SUPABASE_ANON_KEY;

  if (!supabaseUrl || !anonKey) {
    return res.status(500).json({ detail: 'Supabase URL or Key is missing in Vercel settings.' });
  }

  try {
    const response = await fetch(`${supabaseUrl}/auth/v1/signup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'apikey': anonKey,
        'Authorization': `Bearer ${anonKey}`
      },
      body: JSON.stringify({ email: username, password })
    });

    const data = await response.json();
    if (!response.ok) {
      return res.status(400).json({ detail: data.msg || data.error_description || 'Registration failed' });
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
