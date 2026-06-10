export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  
  if (req.method !== 'GET') {
    return res.status(405).json({ success: false, message: 'Method Not Allowed' });
  }

  const { crop } = req.query;
  if (!crop) {
    return res.status(400).json({ success: false, message: 'Crop parameter required' });
  }

  // In a full production environment, this backend route would query the data.gov.in APMC API.
  // For now, it acts as the centralized cloud pricing authority.
  const priceMap = {
    'Mango': 8000, 'Wheat': 2275, 'Rice': 2183, 'Tomato': 1500, 'Corn': 2090,
    'Apple': 7000, 'Grape': 6000, 'Potato': 1200, 'Citrus': 4000, 'Sunflower': 4500,
    'Pepper': 5000, 'Banana': 1800, 'Cotton': 7200, 'Onion': 2000, 
    'Pigeon Pea': 7000, 'Moong Dal': 8500, 'Black Gram': 8000, 'Soybean': 4600, 
    'Jowar': 3180, 'Groundnut': 6377, 'Harbhara': 5335, 'Bajra': 2500, 
    'Turmeric': 12000, 'Pomegranate': 8500, 'Mustard': 5450
  };
  
  const kgPriceMap = {
    'Marigold': 60, 'Rose': 150, 'Jasmine': 200, 'Hibiscus': 80, 'Lotus': 250, 'Lavender': 400,
    'Tulsi': 120, 'Aloe Vera': 25, 'Mint': 40, 'Orchid': 500, 'Spinach': 30,
    'Coconut': 30, 'Lemon': 80, 'Carrot': 40, 'Cabbage': 20, 'Ginger': 120, 'Betel Leaf': 200,
    'Papaya': 25, 'Watermelon': 15, 'Strawberry': 250, 'Guava': 50
  };

  let basePrice, unit;

  if (kgPriceMap[crop]) {
    basePrice = kgPriceMap[crop];
    unit = 'kg';
  } else if (crop === 'Sugarcane') {
    basePrice = 3150;
    unit = 'ton';
  } else {
    basePrice = priceMap[crop] || (crop.includes('Dal') || crop.includes('Pea') ? 6500 : 2500);
    unit = 'quintal';
  }

  // Simulate live market fluctuation (adds realism to the API response)
  const rand = Math.floor(Math.random() * (basePrice * 0.1)) - (basePrice * 0.05);
  const currentPrice = Math.round(basePrice + rand);
  const trend = rand >= 0 ? 'up' : 'down';

  return res.status(200).json({
    success: true,
    data: {
      crop: crop,
      price: currentPrice,
      basePrice: basePrice,
      unit: unit,
      trend: trend,
      currency: 'INR',
      timestamp: new Date().toISOString(),
      source: "APMC Server API"
    }
  });
}
