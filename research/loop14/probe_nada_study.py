import urllib.request
import re

url = 'https://microdata.gov.in/nada/index.php/catalog/237/related-materials'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        html = r.read().decode('utf-8', errors='replace')
        print('Related materials length:', len(html))
        files = re.findall(r'href=[\'"]([^\'"]+\.pdf)[\'"]', html, re.I)
        print('PDFs found in related materials:', len(files), files[:10])
except Exception as e:
    print('Error:', e)
