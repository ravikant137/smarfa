const fs = require('fs');
const path = require('path');

const DATA_FILE = path.join(__dirname, 'data.json');

module.exports = async (req, res) => {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader(
    'Access-Control-Allow-Headers',
    'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version'
  );

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  try {
    if (!fs.existsSync(DATA_FILE)) {
      return res.status(500).json({ success: false, error: "Database not found." });
    }

    const data = JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));

    return res.status(200).json({
      success: true,
      data: data.inventory
    });
  } catch (error) {
    console.error("Inventory API Error:", error);
    return res.status(500).json({ success: false, error: error.message });
  }
};
