export default async function handler(req, res) {
  if (req.method !== 'GET') return res.status(405).json({ error: 'Method Not Allowed' });

  const { q } = req.query;
  if (!q) return res.status(400).json({ error: 'Query parameter "q" is required' });

  try {
    const searchUrl = `https://html.duckduckgo.com/html/?q=${encodeURIComponent(q + ' product bottle')}`;
    const response = await fetch(searchUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
      }
    });

    if (!response.ok) throw new Error('Search failed');

    const html = await response.text();
    // DuckDuckGo HTML image results are usually in <img class="result__image" src="..." /> or similar
    const match = html.match(/<img[^>]+src="([^">]+)"/g);
    
    let imageUrl = null;
    if (match && match.length > 0) {
      for (let imgTag of match) {
        const srcMatch = imgTag.match(/src="([^">]+)"/);
        if (srcMatch && srcMatch[1]) {
          const src = srcMatch[1].replace('&amp;', '&');
          if (src.startsWith('//')) {
            imageUrl = 'https:' + src;
            break;
          } else if (src.startsWith('http')) {
            imageUrl = src;
            break;
          } else if (src.startsWith('/')) {
            imageUrl = 'https://duckduckgo.com' + src;
            break;
          }
        }
      }
    }

    if (imageUrl) {
      res.status(200).json({ url: imageUrl });
    } else {
      res.status(404).json({ error: 'No image found' });
    }
  } catch (error) {
    console.error('Image Search Error:', error);
    res.status(500).json({ error: 'Failed to fetch image' });
  }
}
