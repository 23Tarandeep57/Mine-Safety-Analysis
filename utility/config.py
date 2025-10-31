import os
from pathlib import Path

USER_AGENT = os.environ.get("USER_AGENT", "MineSafetyAgent/1.0 (contact: you@example.com)")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
SUMMARIZER = os.environ.get("SUMMARIZER")

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.environ.get("MONGODB_DB", "mine_safety")
MONGODB_COLLECTION = os.environ.get("MONGODB_COLLECTION", "dgms_reports")

BASE_URL = "https://www.dgms.gov.in/UserView/index?mid=1362"

DATA_DIR = Path("data")
OUTPUT_SUMMARY_PATH = DATA_DIR / "fatal_reports_summary.json"
OUTPUT_PARSED_PATH = DATA_DIR / "parsed_reports.json"
DATA_DIR.mkdir(exist_ok=True, parents=True)
