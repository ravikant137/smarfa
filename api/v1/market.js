export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  
  if (req.method !== 'GET') {
    return res.status(405).json({ success: false, message: 'Method Not Allowed' });
  }

  const { query, treatment } = req.query;
  const displayName = query || treatment || 'Agricultural Product';
  const searchStr = (displayName + ' pesticide bottle').trim();

  try {
    // Dynamically search the web for the product image (simulating Google Images search)
    const searchUrl = `https://images.search.yahoo.com/search/images?p=${encodeURIComponent(searchStr)}`;
    
    const response = await fetch(searchUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
      }
    });

    if (response.ok) {
      const html = await response.text();
      // Extract the first high-quality thumbnail image from search results
      const match = html.match(/src=["'](https:\/\/tse[0-9]\.mm\.bing\.net[^"']+)["']/);
      
      if (match && match[1]) {
        return res.status(200).json({
          success: true,
          data: {
            name: displayName,
            image: match[1],
            company: "Verified Web Result",
            price: "Check Local Store",
            isWebScraped: true
          }
        });
      }
    }
  } catch (error) {
    console.error("Web scraper error:", error);
  }

  // Fallback: Generate dynamic AI product image if web search fails
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
