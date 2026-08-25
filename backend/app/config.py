import os

from dotenv import load_dotenv

load_dotenv()

GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY", "test")
GUARDIAN_API_URL = "https://content.guardianapis.com/search"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./good_brief.db")

# Minimum classifier confidence required to store an article as "positive".
POSITIVE_CONFIDENCE_THRESHOLD = float(os.getenv("POSITIVE_CONFIDENCE_THRESHOLD", "0.6"))
