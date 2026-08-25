import sys
import os
import re

sys.path.append(os.path.abspath("C:/Projects/Positive News Portal/the-good-brief/the-good-brief/backend"))

sys.stdout.reconfigure(encoding='utf-8')

from app.classifier import classify, POSITIVE_TERMS

# Define custom regex to test
_WORD_RE = re.compile(r"[\u0980-\u09ffA-Za-z0-9']+")

def test_tokenize(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())

title = "বাংলাদেশ ক্রিকেট দল বড় জয় পেয়েছে"
summary = "খেলোয়াড়দের অসাধারণ সাফল্যে দেশবাসী আনন্দিত।"

print("Tokens in Title:", test_tokenize(title))
print("Tokens in Summary:", test_tokenize(summary))
