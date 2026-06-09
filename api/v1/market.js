export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  
  if (req.method !== 'GET') {
    return res.status(405).json({ success: false, message: 'Method Not Allowed' });
  }

  const { query, treatment } = req.query;
  const searchStr = (query + ' ' + treatment).toLowerCase();

  // Backend Product Database (Simulating a real e-commerce backend)
  const productsDB = [
    { keys: ["spinosad"], name: "Katyayani Spinosad 2.5% SC", image: "https://m.media-amazon.com/images/I/51r+hXo1RJL._SX679_.jpg", company: "Katyayani Organics", price: "₹450" },
    { keys: ["copper", "blitox"], name: "Blitox 50W Copper Fungicide", image: "https://m.media-amazon.com/images/I/61WfQk5yJQL._SX679_.jpg", company: "Tata Rallis", price: "₹380" },
    { keys: ["neem"], name: "Plantic Organic Neem Oil", image: "https://m.media-amazon.com/images/I/61r5tS0k1JL._SX679_.jpg", company: "Plantic", price: "₹299" },
    { keys: ["imidacloprid", "confidor"], name: "Confidor Imidacloprid", image: "https://m.media-amazon.com/images/I/51T9w9w9pQL._SX679_.jpg", company: "Bayer CropScience", price: "₹520" },
    { keys: ["mancozeb", "dithane"], name: "UPL Indofil M-45 Mancozeb", image: "https://m.media-amazon.com/images/I/71uVv8QOIfL._SX679_.jpg", company: "UPL Ltd", price: "₹310" },
    { keys: ["chlorothalonil", "daconil"], name: "Syngenta Daconil 2787 Fungicide", image: "https://m.media-amazon.com/images/I/41-b0K0P0jL._AC_SY879_.jpg", company: "Syngenta", price: "₹850" },
    { keys: ["trichoderma"], name: "Sanjeevni Trichoderma Viride", image: "https://m.media-amazon.com/images/I/61k2a03rG6L._SX679_.jpg", company: "Katyayani", price: "₹180" },
    { keys: ["azoxystrobin", "amistar"], name: "Amistar Azoxystrobin 23% SC", image: "https://m.media-amazon.com/images/I/51wY84a-mBL._SX679_.jpg", company: "Syngenta", price: "₹1200" },
    { keys: ["tricyclazole", "beam"], name: "Beam 75 WP Tricyclazole", image: "https://m.media-amazon.com/images/I/51D8zD1-mBL._SX679_.jpg", company: "Dow AgroSciences", price: "₹650" }
  ];

  let matchedProduct = null;

  for (let prod of productsDB) {
    for (let key of prod.keys) {
      if (searchStr.includes(key)) {
        matchedProduct = prod;
        break;
      }
    }
    if (matchedProduct) break;
  }

  if (matchedProduct) {
    return res.status(200).json({
      success: true,
      data: matchedProduct
    });
  }

  // Fallback: Generate dynamic AI product image if not in DB
  const displayName = query || treatment || 'Agricultural Product';
  const aiImagePrompt = encodeURIComponent('A professional product photo of an agricultural bottle labeled "' + displayName + '", pesticide chemical, clean white background, high quality');
  const aiFallbackUrl = 'https://image.pollinations.ai/prompt/' + aiImagePrompt + '?nologo=true&width=400&height=400';

  return res.status(200).json({
    success: true,
    data: {
      name: displayName,
      image: aiFallbackUrl,
      company: "Generic Brand",
      price: "Check Local Store",
      isAiGenerated: true
    }
  });
}
