import httpx
import xml.etree.ElementTree as ET
import sys

# Ensure stdout can write utf-8 characters on windows
sys.stdout.reconfigure(encoding='utf-8')

urls = [
    ("The Daily Star", "https://www.thedailystar.net/frontpage/rss.xml"),
    ("BD24Live.com", "https://www.bd24live.com/feed"),
    ("bdnews24.com - Home", "https://bdnews24.com/?widgetName=rssfeed&widgetId=1150&getXmlFeed=true"),
    ("Bangla News", "https://www.banglanews24.com/rss/rss.xml"),
    ("JUGANTOR", "https://www.jugantor.com/feed/rss.xml"),
    ("jagonews24.com", "https://www.jagonews24.com/rss/rss.xml"),
    ("kalerkantho", "https://www.kalerkantho.com/rss.xml"),
    ("prothomalo", "https://www.prothomalo.com/feed/")
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

for name, url in urls:
    try:
        r = httpx.get(url, timeout=10.0, headers=headers, follow_redirects=True)
        print(f"\n=== {name} ({url}) ===")
        print(f"Status: {r.status_code}")
        # Parse XML
        # Some feeds return bad entities like &nbsp; or &mdash; in XML which ET can fail on.
        # Let's clean up common HTML entities from XML content before parsing
        content = r.content
        # ET.fromstring can parse bytes
        root = ET.fromstring(content)
        # Find all <item> or <entry>
        items = root.findall(".//item")
        if not items:
            items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
        
        print(f"Found {len(items)} items")
        if items:
            first = items[0]
            title = first.findtext("title") or first.findtext("{http://www.w3.org/2005/Atom}title")
            link = first.findtext("link") or first.find("link").attrib.get("href") if first.find("link") is not None else ""
            desc = first.findtext("description") or first.findtext("{http://www.w3.org/2005/Atom}summary")
            print(f"  First Title: {title}")
            print(f"  First Desc: {desc[:200] if desc else 'None'}")
    except Exception as e:
        print(f"  Failed: {e}")
