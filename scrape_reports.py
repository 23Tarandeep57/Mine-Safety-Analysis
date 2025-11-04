#!/usr/bin/env python3
import os
import json
from datetime import datetime, timezone
from pymongo.errors import PyMongoError
from utility.config import OUTPUT_PARSED_PATH, MONGODB_DB, MONGODB_COLLECTION
from utility.scraper import scrape_fatal_reports
from utility.extract import extract_text_from_url
from utility.parser import (
    parse_report_to_schema_llm,
    parse_report_to_schema_heuristic,
)
from utility.db import ensure_mongo_collection
from utility.chatbot_utils import initialize_components

# local constants pulled from config module


def process_link(link, coll):
    print(f"→ Fetching: {link['title'][:80]}…")
    text = extract_text_from_url(link["url"])

    # Prefer LLM-based structured extraction when available
    doc = parse_report_to_schema_llm(text, link["url"], link["title"]) or \
          parse_report_to_schema_heuristic(text, link["url"], link["title"])

    # Insert/upsert into MongoDB
    if coll is not None:
        try:
            if doc.get("report_id"):
                coll.replace_one({"report_id": doc["report_id"]}, doc, upsert=True)
            else:
                coll.insert_one(doc)
            print("  Stored in MongoDB")
        except PyMongoError as e:
            print(f" MongoDB write failed: {e}")
    return doc


def collect_all_reports():
    print("Starting DGMS report parser -> MongoDB")
    coll = ensure_mongo_collection()
    if coll is not None:
        print(f"Using MongoDB collection {MONGODB_DB}.{MONGODB_COLLECTION}")
    else:
        print("MongoDB not available — will only write local JSON snapshot.")

    try:
        links = scrape_fatal_reports()
    except Exception as e:
        print(f"Failed to scrape base page: {e}")
        return

    if not links:
        print("No fatal accident report links found.")
        return

    limit = int(os.environ.get("REPORT_LIMIT", "5"))
    parsed_docs = []
    for i, link in enumerate(links[:limit], start=1):
        doc = process_link(link, coll)
        parsed_docs.append(doc)

    # saved a local snapshot
    with open(OUTPUT_PARSED_PATH, "w", encoding="utf-8") as f:
        json.dump(parsed_docs, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(parsed_docs)} structured records to: {OUTPUT_PARSED_PATH}")


def main():
    collect_all_reports()


if __name__ == "__main__":
    main()
