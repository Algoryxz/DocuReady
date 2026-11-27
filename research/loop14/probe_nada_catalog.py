import urllib.request
import re

url = 'https://microdata.gov.in/nada/index.php/catalog'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        html = r.read().decode('utf-8', errors='replace')
        print('Catalog Page Length:', len(html))
        # Find links to studies
        studies = re.findall(r'catalog/(\d+)', html)
        print('Study IDs found:', len(set(studies)), sorted(list(set(studies)))[:10])
except Exception as e:
    print('Error:', e)
