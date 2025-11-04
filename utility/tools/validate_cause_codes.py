#!/usr/bin/env python3
"""
Validate mapped incident_details.cause_code against incident_details.brief_cause for manual review.

This script fetches records where both fields exist and prints them for comparison.

Usage:
  python3 utility/tools/validate_cause_codes.py
  LIMIT=50 python3 utility/tools/validate_cause_codes.py
"""
import os
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, PyMongoError
from dotenv import load_dotenv

load_dotenv()

# --- Constants from config ---
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.environ.get("MONGODB_DB", "mine_safety")
MONGODB_COLLECTION = os.environ.get("MONGODB_COLLECTION", "dgms_reports")

def get_collection():
    """Create a Mongo client, ping the server, and return the target collection."""
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=4000)
        client.admin.command("ping")
        return client[MONGODB_DB][MONGODB_COLLECTION]
    except ServerSelectionTimeoutError:
        print("MongoDB server is not reachable (ServerSelectionTimeout).")
        print(f"URI: {MONGODB_URI}")
        print("Hints: Start MongoDB locally, or set MONGODB_URI to a reachable instance.")
        return None
    except PyMongoError as e:
        print(f"MongoDB error while connecting/pinging: {e}")
        return None

def query_for_validation(limit: int):
    """Query for documents that have both brief_cause and cause_code."""
    coll = get_collection()
    if coll is None:
        return []

    # Query for documents where both fields exist and are not empty
    q = {
        "incident_details.brief_cause": {"$exists": True, "$ne": ""},
        "incident_details.cause_code": {"$exists": True, "$ne": ""},
    }
    
    projection = {
        "report_id": 1,
        "incident_details.brief_cause": 1,
        "incident_details.cause_code": 1,
    }
    
    try:
        cursor = coll.find(q, projection).limit(limit)
        return list(cursor)
    except PyMongoError as e:
        print(f"MongoDB error while querying documents: {e}")
        return []

def main():
    """Main function to fetch and display cause code mappings for validation."""
    limit = int(os.environ.get("LIMIT", "100"))
    print(f"Fetching up to {limit} documents for cause code validation...")
    
    docs = query_for_validation(limit)
    
    if not docs:
        print("No documents found with both `brief_cause` and `cause_code` to validate.")
        return

    print(f"Found {len(docs)} documents. Displaying for review:")
    print("-" * 120)
    print(f"{'REPORT ID':<20} | {'MAPPED CAUSE CODE':<30} | {'BRIEF CAUSE (from text)':<65}")
    print("-" * 120)

    for doc in docs:
        # Ensure variables safely fall back to "N/A" if they are None or empty
        report_id = doc.get("report_id") or str(doc.get("_id")) or "N/A"
        incident_details = doc.get("incident_details", {})
        brief_cause = incident_details.get("brief_cause") or "N/A"
        cause_code = incident_details.get("cause_code") or "N/A"
        
        # Truncate long text for display
        if len(brief_cause) > 60:
            brief_cause = brief_cause[:57] + "..."

        print(f"{report_id:<20} | {cause_code:<30} | {brief_cause:<65}")

    print("-" * 120)
    print(f"Finished. Displayed {len(docs)} records.")


if __name__ == "__main__":
    main()
