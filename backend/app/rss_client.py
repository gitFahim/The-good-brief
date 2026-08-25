import email.utils
from datetime import datetime
import logging
import httpx
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

# List of feeds from the OPML that are active and don't return 403
BANGLADESH_FEEDS = [
    ("The Daily Star", "https://www.thedailystar.net/frontpage/rss.xml"),
    ("BD24Live.com", "https://www.bd24live.com/feed"),
    ("jagonews24.com", "https://www.jagonews24.com/rss/rss.xml")
]

def parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    try:
        return email.utils.parsedate_to_datetime(date_str.strip())
    except Exception:
        try:
            return datetime.fromisoformat(date_str.strip().replace("Z", "+00:00"))
        except Exception:
            return None


def _find_first(item: ET.Element, tags: list[str]) -> ET.Element | None:
    """Return the first matching child element across a list of tag names.

    Do NOT chain item.find(a) or item.find(b): an Element's truthiness in
    ElementTree is based on its number of *child elements*, not its text.
    A plain <link>https://...</link> tag has zero children, so
    bool(link_elem) is False even though it clearly has a value -- `or`
    would silently fall through to the next .find() and lose it. Explicit
    `is None` checks avoid that trap.
    """
    for tag in tags:
        elem = item.find(tag)
        if elem is not None:
            return elem
    return None

def fetch_rss_articles() -> list[dict]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    }
    
    articles = []
    
    for name, url in BANGLADESH_FEEDS:
        try:
            logger.info("Fetching RSS feed: %s (%s)", name, url)
            r = httpx.get(url, timeout=15.0, headers=headers, follow_redirects=True)
            r.raise_for_status()
            
            root = ET.fromstring(r.content)
            items = root.findall(".//item")
            if not items:
                items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
                
            for item in items:
                # Recursive title text extraction
                title_elem = _find_first(item, ["title", "{http://www.w3.org/2005/Atom}title"])
                title = ""
                if title_elem is not None:
                    title = "".join(title_elem.itertext()).strip()
                
                # Link
                link = ""
                link_elem = _find_first(item, ["link", "{http://www.w3.org/2005/Atom}link"])
                if link_elem is not None:
                    if link_elem.text:
                        link = link_elem.text.strip()
                    else:
                        link = link_elem.attrib.get("href", "").strip()
                
                # Summary/Description
                desc_elem = _find_first(item, [
                    "description",
                    "{http://www.w3.org/2005/Atom}summary",
                    "{http://www.w3.org/2005/Atom}content",
                ])
                summary = ""
                if desc_elem is not None:
                    summary = "".join(desc_elem.itertext()).strip()
                
                # Date
                date_elem = _find_first(item, [
                    "pubDate",
                    "{http://www.w3.org/2005/Atom}updated",
                    "{http://www.w3.org/2005/Atom}published",
                ])
                published_at = None
                if date_elem is not None:
                    published_at = parse_date(date_elem.text)
                
                # Image thumbnail if available
                image_url = ""
                media_content = _find_first(item, [
                    ".//{http://search.yahoo.com/mrss/}content",
                    ".//{http://search.yahoo.com/mrss/}thumbnail",
                ])
                if media_content is not None:
                    image_url = media_content.attrib.get("url", "")
                
                if title and link:
                    articles.append({
                        "source": name,
                        "url": link,
                        "title": title,
                        "summary": summary,
                        "section": "Bangladesh",
                        "image_url": image_url,
                        "published_at": published_at,
                    })
        except Exception as e:
            logger.error("Failed to fetch/parse feed %s: %s", name, e)
            
    return articles