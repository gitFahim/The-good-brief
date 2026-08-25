import sys
import os

sys.path.append(os.path.abspath("C:/Projects/Positive News Portal/the-good-brief/the-good-brief/backend"))

sys.stdout.reconfigure(encoding='utf-8')

import httpx
import xml.etree.ElementTree as ET
from app.rss_client import BANGLADESH_FEEDS, parse_date

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

for name, url in BANGLADESH_FEEDS:
    try:
        print(f"\n--- Fetching {name} ---")
        r = httpx.get(url, timeout=15.0, headers=headers, follow_redirects=True)
        r.raise_for_status()
        print("Status:", r.status_code)
        
        # Parse XML
        # Let's see if this throws
        root = ET.fromstring(r.content)
        items = root.findall(".//item")
        if not items:
            items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
        print("Found items:", len(items))
    except Exception as e:
        print("Failed:", type(e), e)
