const https = require('https');

https.get('https://html.duckduckgo.com/html/?q=katyayani+spinosad+bottle', (res) => {
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => {
    const match = data.match(/<img[^>]+src="([^">]+)"/g);
    if (match) {
      console.log('Images found:', match.slice(0, 3));
    } else {
      console.log('No image found');
    }
  });
}).on('error', console.error);
