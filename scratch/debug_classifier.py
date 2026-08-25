import sys
import os

sys.path.append(os.path.abspath("C:/Projects/Positive News Portal/the-good-brief/the-good-brief/backend"))

# Reconfigure stdout to use UTF-8 representation
sys.stdout.reconfigure(encoding='utf-8')

from app.classifier import classify, _tokenize, _score_sentence, POSITIVE_TERMS, NEGATIVE_TERMS

title = "বাংলাদেশ ক্রিকেট দল বড় জয় পেয়েছে"
summary = "খেলোয়াড়দের অসাধারণ সাফল্যে দেশবাসী আনন্দিত।"

print("Tokens in Title:", _tokenize(title))
print("Score of Title:", _score_sentence(title))
print("Tokens in Summary:", _tokenize(summary))
print("Score of Summary:", _score_sentence(summary))
print("Classify Result:", classify(title, summary))

# Let's inspect POSITIVE_TERMS keys
print("\nIs 'সাফল্য' in POSITIVE_TERMS?:", "সাফল্য" in POSITIVE_TERMS)
print("Is 'জয়' in POSITIVE_TERMS?:", "জয়" in POSITIVE_TERMS)
print("Is 'জয়' in POSITIVE_TERMS?:", "জয়" in POSITIVE_TERMS)
