import os
from pathlib import Path

# User Agent for web requests
USER_AGENT = os.environ.get("USER_AGENT", "MineSafetyAgent/1.0 (contact: deeptaran2004bti@gmail.com)")

# LLM Configuration
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
SUMMARIZER = os.environ.get("SUMMARIZER")

# MongoDB Configuration
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.environ.get("MONGODB_DB", "mine_safety")
MONGODB_COLLECTION = os.environ.get("MONGODB_COLLECTION", "dgms_reports")

# Redis Configuration
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

# DGMS Website
BASE_URL = "https://www.dgms.gov.in/UserView/index?mid=1362"

# Data Directories
DATA_DIR = Path("data")
OUTPUT_SUMMARY_PATH = DATA_DIR / "fatal_reports_summary.json"
OUTPUT_PARSED_PATH = DATA_DIR / "parsed_reports.json"
DATA_DIR.mkdir(exist_ok=True, parents=True)

# Chat/API Configuration
CHAT_TIMEOUT_SECONDS = int(os.environ.get("CHAT_TIMEOUT_SECONDS", "120"))
QA_TIMEOUT_SECONDS = int(os.environ.get("QA_TIMEOUT_SECONDS", "60"))

# Periodic Task Intervals (in seconds)
ANALYSIS_INTERVAL_SECONDS = int(os.environ.get("ANALYSIS_INTERVAL_SECONDS", "900"))  # 15 minutes
REPORT_GENERATION_INTERVAL_SECONDS = int(os.environ.get("REPORT_GENERATION_INTERVAL_SECONDS", "86400"))  # 24 hours

# Embedding/Chunking Configuration
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "models/text-embedding-004")
LLM_MODEL = os.environ.get("LLM_MODEL", "models/gemini-2.5-flash")
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "2000"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "400"))

# Chat History
MAX_CHAT_HISTORY = int(os.environ.get("MAX_CHAT_HISTORY", "50"))
