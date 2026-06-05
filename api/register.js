export default function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ detail: 'Method Not Allowed' });

  res.status(200).json({ 
    status: 'success', 
    message: 'User registered successfully!' 
  });
}
