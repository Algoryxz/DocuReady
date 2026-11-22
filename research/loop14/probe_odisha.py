import urllib.request
import re

url = 'https://scholarship.odisha.gov.in/website/home'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        html = r.read().decode('utf-8', errors='replace')
        print('Odisha scholarship home length:', len(html))
        pdfs = re.findall(r'href=[\'"]([^\'"]+\.pdf)[\'"]', html, re.I)
        print('PDF links found:', len(pdfs), pdfs[:10])
except Exception as e:
    print('Error:', e)
