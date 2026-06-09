import urllib.request
import urllib.parse
import re
import base64
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

products = [
    "Katyayani Spinosad 2.5 SC pesticide bottle",
    "Blitox 50W Copper Fungicide Tata bottle",
    "Plantic Organic Neem Oil bottle",
    "Confidor Imidacloprid Bayer bottle",
    "UPL Indofil M-45 Mancozeb bottle",
    "Syngenta Daconil Fungicide bottle",
    "Sanjeevni Trichoderma Viride bottle",
    "Amistar Azoxystrobin Syngenta bottle",
    "Beam 75 WP Tricyclazole bottle"
]

db = {}

for prod in products:
    try:
        url = "https://images.search.yahoo.com/search/images?p=" + urllib.parse.quote(prod)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        html = urllib.request.urlopen(req, context=ctx).read().decode('utf-8')
        match = re.search(r'src=["\'](https://tse[0-9]\.mm\.bing\.net[^"\']+)["\']', html)
        if match:
            img_url = match.group(1)
            img_req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
            img_data = urllib.request.urlopen(img_req, context=ctx).read()
            b64 = "data:image/jpeg;base64," + base64.b64encode(img_data).decode('utf-8')
            db[prod] = b64
            print("Success for", prod)
        else:
            print("No match for", prod)
    except Exception as e:
        print("Error on", prod, e)

with open('b64_db.json', 'w') as f:
    json.dump(db, f)

