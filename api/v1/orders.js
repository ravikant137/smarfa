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

    let data = JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));

    // Handle GET /orders
    if (req.method === 'GET') {
      return res.status(200).json({
        success: true,
        data: data.orders
      });
    }

    // Handle POST /orders (Checkout)
    if (req.method === 'POST') {
      let body = '';
      req.on('data', chunk => { body += chunk.toString(); });
      req.on('end', () => {
        try {
          const orderReq = JSON.parse(body);
          const { storeName, product, price, quantity, customerDetails } = orderReq;

          // 1. Find store and validate stock
          const storeIndex = data.inventory.findIndex(s => s.name === storeName);
          if (storeIndex === -1) {
            return res.status(404).json({ success: false, error: "Store not found." });
          }

          const store = data.inventory[storeIndex];
          if (store.stock < quantity) {
            return res.status(400).json({ success: false, error: "Insufficient stock at this store." });
          }

          // 2. Deduct stock
          data.inventory[storeIndex].stock -= quantity;

          // 3. Create Order
          const newOrder = {
            id: 'ORD-' + Math.random().toString(36).substr(2, 9).toUpperCase(),
            storeName,
            product,
            price,
            quantity,
            totalAmount: (parseInt(price.replace(/[^0-9]/g, '')) * quantity),
            customer: customerDetails || 'Guest User',
            status: 'Processing',
            date: new Date().toISOString()
          };

          data.orders.push(newOrder);

          // 4. Save to DB
          fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));

          return res.status(200).json({
            success: true,
            order: newOrder
          });
        } catch (err) {
          return res.status(400).json({ success: false, error: "Invalid JSON format." });
        }
      });
    }
  } catch (error) {
    console.error("Orders API Error:", error);
    return res.status(500).json({ success: false, error: error.message });
  }
};
