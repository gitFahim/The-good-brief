from app.rss_client import BANGLADESH_FEEDS


def test_daily_star_feed_is_configured():
    assert ("The Daily Star", "https://www.thedailystar.net/frontpage/rss.xml") in BANGLADESH_FEEDS


def test_bangladesh_feeds_are_named():
    assert all(name and url.startswith(("http://", "https://")) for name, url in BANGLADESH_FEEDS)
