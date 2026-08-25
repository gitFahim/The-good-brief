from app.dedup import deduplicate, is_duplicate, normalize_title


def test_same_url_is_duplicate():
    a = {"url": "https://x.com/a", "title": "Story one"}
    b = {"url": "https://x.com/a", "title": "Story one (updated)"}
    assert is_duplicate(a, b) is True


def test_near_identical_titles_are_duplicate():
    a = {"url": "https://x.com/a", "title": "Local hospital opens new wing!"}
    b = {"url": "https://y.com/b", "title": "Local hospital opens new wing"}
    assert is_duplicate(a, b) is True


def test_different_stories_are_not_duplicate():
    a = {"url": "https://x.com/a", "title": "Local hospital opens new wing"}
    b = {"url": "https://y.com/b", "title": "City announces new park funding"}
    assert is_duplicate(a, b) is False


def test_normalize_title_strips_punctuation_and_case():
    assert normalize_title("Hello, World!!") == "hello world"


def test_deduplicate_keeps_first_occurrence_only():
    articles = [
        {"url": "https://x.com/a", "title": "Big win for local team"},
        {"url": "https://x.com/a", "title": "Big win for local team (updated)"},
        {"url": "https://y.com/b", "title": "Completely different headline"},
    ]
    result = deduplicate(articles)
    assert len(result) == 2
    assert result[0]["url"] == "https://x.com/a"
