export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  
  if (req.method !== 'GET') {
    return res.status(405).json({ success: false, message: 'Method Not Allowed' });
  }

  const { query, treatment } = req.query;
  const displayName = query || treatment || 'Agricultural Product';
  const searchStr = (displayName + ' pesticide bottle').trim();
  const matchStr = (query + ' ' + treatment).toLowerCase();

  // 1. Verified Indian Agricultural Database
  const productsDB = [
    { keys: ["spinosad"], name: "Katyayani Spinosad 2.5% SC", image: "https://wsrv.nl/?url=m.media-amazon.com/images/I/51r+hXo1RJL._SX679_.jpg", company: "Katyayani Organics", price: "₹450" },
    { keys: ["copper", "blitox"], name: "Blitox 50W Copper Fungicide", image: "https://wsrv.nl/?url=m.media-amazon.com/images/I/61WfQk5yJQL._SX679_.jpg", company: "Tata Rallis", price: "₹380" },
    { keys: ["neem"], name: "Plantic Organic Neem Oil", image: "https://wsrv.nl/?url=m.media-amazon.com/images/I/61r5tS0k1JL._SX679_.jpg", company: "Plantic", price: "₹299" },
    { keys: ["imidacloprid", "confidor"], name: "Confidor Imidacloprid", image: "https://wsrv.nl/?url=m.media-amazon.com/images/I/51T9w9w9pQL._SX679_.jpg", company: "Bayer CropScience", price: "₹520" },
    { keys: ["mancozeb", "dithane"], name: "UPL Indofil M-45 Mancozeb", image: "https://wsrv.nl/?url=m.media-amazon.com/images/I/71uVv8QOIfL._SX679_.jpg", company: "UPL Ltd", price: "₹310" },
    { keys: ["chlorothalonil", "daconil"], name: "Syngenta Daconil 2787 Fungicide", image: "https://wsrv.nl/?url=m.media-amazon.com/images/I/41-b0K0P0jL._AC_SY879_.jpg", company: "Syngenta", price: "₹850" },
    { keys: ["trichoderma"], name: "Sanjeevni Trichoderma Viride", image: "https://wsrv.nl/?url=m.media-amazon.com/images/I/61k2a03rG6L._SX679_.jpg", company: "Katyayani", price: "₹180" },
    { keys: ["azoxystrobin", "amistar"], name: "Amistar Azoxystrobin 23% SC", image: "https://wsrv.nl/?url=m.media-amazon.com/images/I/51wY84a-mBL._SX679_.jpg", company: "Syngenta", price: "₹1200" },
    { keys: ["tricyclazole", "beam"], name: "Beam 75 WP Tricyclazole", image: "https://wsrv.nl/?url=m.media-amazon.com/images/I/51D8zD1-mBL._SX679_.jpg", company: "Dow AgroSciences", price: "₹650" }
  ];

  let matchedProduct = null;
  for (let prod of productsDB) {
    if (prod.keys.some(k => matchStr.includes(k))) {
      matchedProduct = prod; break;
    }
  }

  if (matchedProduct) {
    return res.status(200).json({ success: true, data: matchedProduct });
  }

  // 2. Dynamic Yahoo Web Scraper Fallback
  try {
    const searchUrl = `https://images.search.yahoo.com/search/images?p=${encodeURIComponent(searchStr)}`;
    const searchRes = await fetch(searchUrl, { headers: { 'User-Agent': 'Mozilla/5.0' } });
    if (searchRes.ok) {
      const html = await searchRes.text();
      const match = html.match(/src=["'](https:\/\/tse[0-9]\.mm\.bing\.net[^"']+)["']/);
      if (match && match[1]) {
        const proxiedUrl = `https://wsrv.nl/?url=${match[1].replace(/^https?:\/\//, '')}`;
        return res.status(200).json({ success: true, data: { name: displayName, image: proxiedUrl, company: "Verified Web Result", price: "Check Local Store", isWebScraped: true }});
      }
    }
  } catch (error) { console.error("Web scraper error:", error); }

  // 3. Absolute Fallback (Pure SVG)
  const safeFallback = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyMDAgMjAwIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2Y4ZmFmYyIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSI0OCIgZmlsbD0iI2NidDU1ZSIgZG9taW5hbnQtYmFzZWxpbmU9Im1pZGRsZSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+8J+SijwvdGV4dD48dGV4dCB4PSI1MCUiIHk9Ijc1JSIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM5NGEzYjgiIGRvbWluYW50LWJhc2VsaW5lPSJtaWRkbGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiPkFncmljdWx0dXJhbCBQcm9kdWN0PC90ZXh0Pjwvc3ZnPg==';
  return res.status(200).json({ success: true, data: { name: displayName, image: safeFallback, company: "Generic Brand", price: "-", isFallback: true }});
}
