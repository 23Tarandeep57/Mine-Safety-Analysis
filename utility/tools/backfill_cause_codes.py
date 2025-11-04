#!/usr/bin/env python3
"""
Backfill missing incident_details.cause_code in MongoDB by mapping from incident_details.brief_cause
using the local cause_code_db vector store.

Usage:
    python3 utility/tools/backfill_cause_codes.py           # live updates
    DRY_RUN=1 python3 utility/tools/backfill_cause_codes.py # preview only
    LIMIT=100 python3 utility/tools/backfill_cause_codes.py # limit documents processed

Environment variables:
    - MONGODB_URI           (default: mongodb://localhost:27017)
    - MONGODB_DB            (default: mine_safety)
    - MONGODB_COLLECTION    (default: dgms_reports)
    - DRY_RUN               (0/1)
    - LIMIT                 (int)
"""
import os
from typing import Any, Dict
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, PyMongoError
from dotenv import load_dotenv

from find_cause_code import FindCauseCodeTool

load_dotenv()

# --- Constants from config ---
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.environ.get("MONGODB_DB", "mine_safety")
MONGODB_COLLECTION = os.environ.get("MONGODB_COLLECTION", "dgms_reports")


def get_collection():
    """Create a Mongo client, ping the server, and return the target collection.

    Returns:
        Collection object if reachable, else None.
    """
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=4000)
        # Fail fast if server is unreachable
        client.admin.command("ping")
        return client[MONGODB_DB][MONGODB_COLLECTION]
    except ServerSelectionTimeoutError as e:
        print("MongoDB server is not reachable (ServerSelectionTimeout).")
        print(f"URI: {MONGODB_URI}")
        print("Hints: Start MongoDB locally, or set MONGODB_URI to a reachable instance.")
        print("  - On Linux (systemd): sudo systemctl start mongod")
        print("  - Or use Docker: docker run -d -p 27017:27017 --name mongo mongo:6")
        print(f"Details: {e}")
        return None
    except PyMongoError as e:
        print("MongoDB error while connecting/pinging:", e)
        return None


def query_missing(limit: int):
    coll = get_collection()
    if coll is None:
        return None, []
    # Missing or empty cause_code under incident_details
    q = {
        "$or": [
            {"incident_details.cause_code": {"$exists": False}},
            {"incident_details.cause_code": {"$eq": ""}},
            {"incident_details.cause_code": None},
        ]
    }
    try:
        cur = coll.find(q, {"incident_details": 1, "report_id": 1}).limit(limit)
        return coll, list(cur)
    except PyMongoError as e:
        print("MongoDB error while querying documents:", e)
        return coll, []


def backfill_one(coll, finder: FindCauseCodeTool, doc: Dict[str, Any], dry: bool = False) -> bool:
    inc = (doc.get("incident_details") or {})
    brief = (inc.get("brief_cause") or "").strip()
    if not brief:
        return False
    code = finder.use(brief)
    if not code:
        return False
    if dry:
        print(f"→ DRY RUN: Would set cause_code='{code}' for report_id={doc.get('report_id', '<no-id>')}")
        return True
    try:
        coll.update_one({"_id": doc["_id"]}, {"$set": {"incident_details.cause_code": code}})
        print(f"✓ Updated report_id={doc.get('report_id', str(doc.get('_id')))} cause_code={code}")
        return True
    except Exception as e:
        print(f"✗ Failed to update {doc.get('report_id', str(doc.get('_id')))}: {e}")
        return False


def main():
    limit = int(os.environ.get("LIMIT", "200"))
    dry = os.environ.get("DRY_RUN", "0").lower() in ("1", "true", "yes")
    coll, docs = query_missing(limit)
    if coll is None:
        # Connection guidance already printed in get_collection()
        return
    if not docs:
        print("No documents with missing/empty cause_code.")
        return
    print(f"Found {len(docs)} documents missing cause_code. Processing…")
    try:
        finder = FindCauseCodeTool()
    except Exception as e:
        print("Failed to initialize FindCauseCodeTool:", e)
        return
    updated = 0
    for d in docs:
        if backfill_one(coll, finder, d, dry=dry):
            updated += 1
    print(f"Done. Updated {updated}/{len(docs)} docs.")


if __name__ == "__main__":
    main()
