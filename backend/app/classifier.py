"""
Heuristic contextual classifier for "positive news" detection.

Not a pure keyword matcher: it works sentence-by-sentence, detects negation
("did not improve"), weighs semantic frames ("X cured", "X collapses"),
and combines per-sentence scores into a single confidence score for the
whole article. It exposes a small interface (`classify`) so it can be
swapped later for a real LLM-backed classifier without touching callers.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

Label = Literal["positive", "neutral", "negative"]

# Words/phrases with an inherent positive or negative charge, weighted.
POSITIVE_TERMS: dict[str, float] = {
    "breakthrough": 2.0, "cure": 2.0, "cured": 2.0, "recover": 1.5, "recovers": 1.5,
    "recovery": 1.5, "rescued": 1.5, "saved": 1.5, "donates": 1.2,
    "donated": 1.2, "volunteers": 1.0, "celebrates": 1.0, "wins": 1.0,
    "won": 1.0, "record high": 1.2, "improves": 1.2, "improved": 1.2,
    "improving": 1.2, "hope": 1.0, "inspiring": 1.5, "success": 1.2,
    "successful": 1.2, "life-saving": 2.0, "milestone": 1.2,
    "innovative": 1.0, "generous": 1.2, "reunited": 1.5, "thrives": 1.2,
    "thriving": 1.2, "restored": 1.0, "grant": 0.8, "funding boost": 1.0,
    "reforestation": 1.0, "renewable": 0.8, "vaccine": 1.0,
    "protects": 1.0, "protected": 1.0, "clean energy": 1.0,
    "conservation": 0.8, "healed": 1.5, "welcomed": 0.8,
    "triumph": 1.5, "achievement": 1.2, "achieve": 1.2, "achieved": 1.2,
    "creative": 1.0, "discover": 1.0, "discovery": 1.2, "launch": 0.8,
    "partnership": 1.0, "support": 0.8, "progress": 1.0, "benefit": 1.0,
    "help": 0.8, "healthy": 1.0, "happy": 1.0, "love": 1.2,
    "peace": 1.2, "art": 0.6, "music": 0.6, "festival": 0.8,
    "best": 0.8, "popular": 0.8, "tourism": 0.8, "travel": 0.6,
    "delicious": 1.0, "beautiful": 1.2, "stunning": 1.2, "gorgeous": 1.2,
    "wonderful": 1.2, "excellent": 1.2, "amazing": 1.2, "delightful": 1.2,
    "charming": 1.0, "lovely": 1.2, "friendly": 1.0, "kindness": 1.5,
    "সাফল্য": 1.5, "সফল": 1.2, "জয়ী": 1.5, "জয়": 1.2, "উন্নতি": 1.2, "উন্নত": 1.0,
    "সুযোগ": 1.0, "পুরস্কার": 1.5, "উদ্বোধন": 1.0, "আশা": 1.2, "রক্ষা": 1.0,
    "হাসি": 1.2, "আনন্দ": 1.5, "সুন্দর": 1.2, "ভালো": 1.0, "ইতিবাচক": 1.2,
    "স্বীকৃতি": 1.2, "উদার": 1.2, "সহায়তা": 1.0, "দান": 1.2, "রেকর্ড": 1.2,
    "উত্তরণ": 1.0, "অর্জন": 1.2,
}

NEGATIVE_TERMS: dict[str, float] = {
    "dies": 2.0, "died": 2.0, "killed": 2.5, "murder": 2.5, "attack": 1.8,
    "attacks": 1.8, "war": 1.8, "collapse": 1.8, "collapses": 1.8,
    "crisis": 1.5, "disaster": 2.0, "fraud": 1.5, "scandal": 1.5,
    "layoffs": 1.5, "layoff": 1.5, "recession": 1.5, "outbreak": 1.5,
    "shortage": 1.2, "corruption": 1.5, "collapsed": 1.8, "banned": 1.0,
    "protest": 0.8, "protests": 0.8, "violence": 2.0, "arrested": 1.2,
    "sued": 1.0, "lawsuit": 0.8, "decline": 1.0, "declined": 1.0,
    "warns": 0.8, "warning": 0.8, "threat": 1.2, "threatens": 1.2,
    "মৃত্যু": 2.0, "মৃত": 1.5, "নিহত": 2.5, "খুন": 2.5, "ধর্ষণ": 2.5, "হামলা": 1.8,
    "ধ্বংস": 1.8, "দুর্ঘটনা": 2.0, "গ্রেফতার": 1.2, "গ্রেপ্তার": 1.2, "সন্ত্রাস": 2.0,
    "আটক": 1.2, "অভিযোগ": 1.0, "মামলা": 1.0, "তদন্ত": 0.8, "উদ্বেগ": 1.2,
    "ঝুঁকি": 1.2, "সংকট": 1.5, "ক্ষতি": 1.2, "চুরি": 1.5, "ডাকাতি": 1.5,
    "দুর্নীতি": 1.8, "সংঘর্ষ": 1.5, "উচ্ছেদ": 1.5, "পতন": 1.5, "অসুস্থ": 1.0,
    "মহামারী": 1.5,
}

# Normalize terms to NFC format
POSITIVE_TERMS = {unicodedata.normalize('NFC', k): v for k, v in POSITIVE_TERMS.items()}
NEGATIVE_TERMS = {unicodedata.normalize('NFC', k): v for k, v in NEGATIVE_TERMS.items()}

NEGATION_WORDS = {
    "not", "no", "never", "n't", "without", "fails", "failed", "failing",
    "lacks", "unable",
}

# A negation flips the charge of terms that follow within this many tokens.
NEGATION_WINDOW = 3

_WORD_RE = re.compile(r"[\u0980-\u09ffA-Za-z0-9']+")


def _tokenize(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


def _sentence_split(text: str) -> list[str]:
    # Simple sentence splitter; good enough for headline/summary-length text.
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p]


def _score_sentence(sentence: str) -> float:
    """Return a signed score for one sentence: >0 positive, <0 negative."""
    tokens = _tokenize(sentence)
    score = 0.0

    # Check multi-word terms first (phrase matching over the raw sentence).
    lowered = sentence.lower()
    for phrase, weight in POSITIVE_TERMS.items():
        if " " in phrase and phrase in lowered:
            score += weight
    for phrase, weight in NEGATIVE_TERMS.items():
        if " " in phrase and phrase in lowered:
            score -= weight

    for i, tok in enumerate(tokens):
        negated = any(
            neg in tokens[max(0, i - NEGATION_WINDOW):i]
            for neg in NEGATION_WORDS
        )
        
        # Check POSITIVE_TERMS with prefix matching (stemming-like behavior)
        matched_pos = False
        for term, weight in POSITIVE_TERMS.items():
            if " " not in term:
                if tok == term or (len(term) >= 2 and tok.startswith(term)):
                    score += -weight if negated else weight
                    matched_pos = True
                    break
        
        if not matched_pos:
            # Check NEGATIVE_TERMS with prefix matching
            for term, weight in NEGATIVE_TERMS.items():
                if " " not in term:
                    if tok == term or (len(term) >= 2 and tok.startswith(term)):
                        score += weight * 0.5 if negated else -weight
                        break

    return score


@dataclass
class Classification:
    label: Label
    confidence: float  # 0.0 - 1.0
    score: float  # raw signed score, for debugging/ranking


def classify(title: str, summary: str = "") -> Classification:
    """Classify an article as positive / neutral / negative.

    Combines a title score (weighted higher, since headlines carry most
    of the framing) with a summary score across all its sentences.
    """
    title = unicodedata.normalize('NFC', title)
    summary = unicodedata.normalize('NFC', summary)
    
    title_score = _score_sentence(title) * 1.5
    summary_sentences = _sentence_split(summary)
    summary_score = sum(_score_sentence(s) for s in summary_sentences)

    total = title_score + summary_score
    # Normalize into a bounded confidence score with a soft cap.
    magnitude = min(abs(total) / 4.0, 1.0)

    if total > 0.75:
        label: Label = "positive"
        confidence = 0.5 + magnitude * 0.5
    elif total < -0.75:
        label = "negative"
        confidence = 0.5 + magnitude * 0.5
    else:
        label = "neutral"
        # Confidence in "neutral" is highest near zero, falls off near the
        # +/-0.75 boundary.
        confidence = 1.0 - min(abs(total) / 0.75, 1.0) * 0.5

    return Classification(label=label, confidence=round(confidence, 3), score=round(total, 3))
