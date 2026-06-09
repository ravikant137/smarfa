import urllib.request
import re
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch_image(query):
    try:
        url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query + " site:indiamart.com")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req, context=ctx).read().decode('utf-8')
        links = re.findall(r'href="([^"]+)"', html)
        for link in links:
            if "indiamart.com/proddetail/" in link:
                prod_url = urllib.parse.unquote(link.split("uddg=")[1].split("&")[0])
                req = urllib.request.Request(prod_url, headers={'User-Agent': 'Mozilla/5.0'})
                prod_html = urllib.request.urlopen(req, context=ctx).read().decode('utf-8')
                img_match = re.search(r'src="(https://5.imimg.com/[^"]+)"', prod_html)
                if img_match:
                    return img_match.group(1)
    except Exception as e:
        return str(e)
    return None

queries = [
    "Katyayani Spinosad", "Blitox 50W", "Plantic Organic Neem Oil",
    "Confidor Imidacloprid", "Indofil M-45 Mancozeb", "Syngenta Daconil",
    "Sanjeevni Trichoderma", "Amistar Azoxystrobin", "Beam 75 WP"
]

results = {}
for q in queries:
    results[q] = fetch_image(q)

print(json.dumps(results, indent=2))
