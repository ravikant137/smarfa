export default function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ detail: 'Method Not Allowed' });

  const { username } = req.body || {};
  
  res.status(200).json({ 
    status: 'login successful', 
    user_id: 9999,
    username: username || 'demo_user'
  });
}
