from app.classifier import classify


def test_clear_positive_story():
    result = classify(
        "Breakthrough cure gives hope to thousands of patients",
        "Doctors say the treatment has cured patients and inspired new research.",
    )
    assert result.label == "positive"
    assert result.confidence >= 0.6


def test_clear_negative_story():
    result = classify(
        "Dozens killed as violence erupts amid crisis",
        "Officials warn the disaster could trigger a wider war.",
    )
    assert result.label == "negative"


def test_neutral_factual_story():
    result = classify(
        "City council to meet on Thursday",
        "The meeting will discuss the annual budget schedule.",
    )
    assert result.label == "neutral"


def test_negation_flips_positive_term_to_negative():
    result = classify("Patients did not recover after treatment fails")
    assert result.score < 0


def test_negated_negative_term_reads_less_negative():
    plain = classify("Ten people were killed in the attack")
    negated = classify("No one was killed in the incident")
    assert negated.score > plain.score


def test_bengali_positive_story():
    result = classify("বাংলাদেশ ক্রিকেট দল বড় জয় পেয়েছে", "খেলোয়াড়দের অসাধারণ সাফল্যে দেশবাসী আনন্দিত।")
    assert result.label == "positive"


def test_bengali_negative_story():
    result = classify("সড়ক দুর্ঘটনায় পাঁচজন নিহত", "পুলিশ ঘটনার তদন্ত শুরু করেছে।")
    assert result.label == "negative"

