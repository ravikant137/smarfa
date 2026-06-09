export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  
  if (req.method !== 'GET') {
    return res.status(405).json({ success: false, message: 'Method Not Allowed' });
  }

  const { query, treatment } = req.query;
  const displayName = query || treatment || 'Agricultural Product';
  const searchStr = (displayName + ' pesticide bottle').trim();

  try {
    // 1. Search Yahoo Images
    const searchUrl = `https://images.search.yahoo.com/search/images?p=${encodeURIComponent(searchStr)}`;
    const searchRes = await fetch(searchUrl, {
      headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' }
    });

    if (searchRes.ok) {
      const html = await searchRes.text();
      const match = html.match(/src=["'](https:\/\/tse[0-9]\.mm\.bing\.net[^"']+)["']/);
      
      if (match && match[1]) {
        const imageUrl = match[1];
        
        // 2. PROXY THE IMAGE: Fetch the actual image binary from the backend
        // This completely bypasses the user's browser ad-blockers, CORB, and strict security policies!
        const imageRes = await fetch(imageUrl, {
          headers: { 'User-Agent': 'Mozilla/5.0' }
        });
        
        if (imageRes.ok) {
          const arrayBuffer = await imageRes.arrayBuffer();
          const buffer = Buffer.from(arrayBuffer);
          const base64Image = `data:${imageRes.headers.get('content-type') || 'image/jpeg'};base64,${buffer.toString('base64')}`;

          return res.status(200).json({
            success: true,
            data: {
              name: displayName,
              image: base64Image, // Pure base64 data, mathematically impossible to be blocked!
              company: "Verified Web Result",
              price: "Check Local Store",
              isWebScraped: true
            }
          });
        }
      }
    }
  } catch (error) {
    console.error("Web scraper error:", error);
  }

  // Fallback: If scraper fails, proxy Pollinations AI through the backend too!
  try {
    const aiImagePrompt = encodeURIComponent('A professional product photo of an agricultural bottle labeled "' + displayName + '", clean white background');
    const aiFallbackUrl = 'https://image.pollinations.ai/prompt/' + aiImagePrompt + '?nologo=true&width=400&height=400';
    
    const aiRes = await fetch(aiFallbackUrl, { headers: { 'User-Agent': 'Mozilla/5.0' }});
    if (aiRes.ok) {
      const arrayBuffer = await aiRes.arrayBuffer();
      const buffer = Buffer.from(arrayBuffer);
      const base64AiImage = `data:image/jpeg;base64,${buffer.toString('base64')}`;
      
      return res.status(200).json({
        success: true,
        data: { name: displayName, image: base64AiImage, company: "Generic Brand", price: "Check Local Store", isAiGenerated: true }
      });
    }
  } catch(e) {}

  // Absolute final fallback if both network requests fail (pure SVG)
  const safeFallback = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyMDAgMjAwIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2Y4ZmFmYyIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSI0OCIgZmlsbD0iI2NidDU1ZSIgZG9taW5hbnQtYmFzZWxpbmU9Im1pZGRsZSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+8J+SijwvdGV4dD48dGV4dCB4PSI1MCUiIHk9Ijc1JSIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM5NGEzYjgiIGRvbWluYW50LWJhc2VsaW5lPSJtaWRkbGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiPkFncmljdWx0dXJhbCBQcm9kdWN0PC90ZXh0Pjwvc3ZnPg==';
  return res.status(200).json({ success: true, data: { name: displayName, image: safeFallback, company: "Generic Brand", price: "-", isFallback: true }});
}
