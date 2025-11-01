#!/usr/bin/env python3
import os
import re
from typing import Tuple, List
from pymongo import MongoClient

from utility.config import (
    MONGODB_URI,
    MONGODB_DB,
    MONGODB_COLLECTION,
)

# --- Heuristics Data ---

INDIAN_STATES = {
    "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh",
    "goa", "gujarat", "haryana", "himachal pradesh", "jharkhand", "karnataka",
    "kerala", "madhya pradesh", "maharashtra", "manipur", "meghalaya", "mizoram",
    "nagaland", "odisha", "orissa", "punjab", "rajasthan", "sikkim", "tamil nadu",
    "telangana", "tripura", "uttar pradesh", "uttarakhand", "west bengal",
    "andaman and nicobar islands", "chandigarh", "dadra and nagar haveli and daman and diu",
    "delhi", "jammu and kashmir", "ladakh", "lakshadweep", "puducherry"
}

STATE_ABBREV = {
    "mp": "Madhya Pradesh", "up": "Uttar Pradesh", "uk": "Uttarakhand",
    "tn": "Tamil Nadu", "ap": "Andhra Pradesh", "tel": "Telangana",
    "wb": "West Bengal", "mh": "Maharashtra", "gj": "Gujarat",
    "rj": "Rajasthan", "ka": "Karnataka", "kl": "Kerala",
    "ct": "Chhattisgarh", "cg": "Chhattisgarh", "od": "Odisha",
    "pb": "Punjab", "hr": "Haryana", "jk": "Jammu and Kashmir",
}

DISTRICT_TO_STATE = {
    "korba": "Chhattisgarh", "raigarh": "Chhattisgarh", "bilaspur": "Chhattisgarh",
    "dhanbad": "Jharkhand", "ramgarh": "Jharkhand", "bokaro": "Jharkhand",
    "hazaribagh": "Jharkhand", "giridih": "Jharkhand", "east singhbhum": "Jharkhand",
    "west singhbhum": "Jharkhand", "singhbhum": "Jharkhand", "keonjhar": "Odisha",
    "kendujhar": "Odisha", "sundargarh": "Odisha", "angul": "Odisha",
    "jharsuguda": "Odisha", "koraput": "Odisha", "balaghat": "Madhya Pradesh",
    "singrauli": "Madhya Pradesh", "sonbhadra": "Uttar Pradesh", "nagpur": "Maharashtra",
    "yavatmal": "Maharashtra", "ballari": "Karnataka", "bellary": "Karnataka",
    "kolar": "Karnataka", "kadapa": "Andhra Pradesh", "chittorgarh": "Rajasthan",
    "jodhpur": "Rajasthan", "barmer": "Rajasthan", "bikaner": "Rajasthan",
    "kutch": "Gujarat", "kutchh": "Gujarat",
}

# --- Core Logic ---

def mongo_collection():
    """Connects to the MongoDB collection."""
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=4000)
    return client[MONGODB_DB][MONGODB_COLLECTION]

def find_missing_docs(coll, limit: int) -> list:
    """Finds documents with missing or blank location fields."""
    blank_like = {"$regex": r"^\s*(?:na|n/?a|nil|not available|-)?\s*$", "$options": "i"}
    query = {
        "$or": [
            {"mine_details.district": {"$exists": False}},
            {"mine_details.state": {"$exists": False}},
            {"mine_details.district": {"$in": ["", None]}},
            {"mine_details.state": {"$in": ["", None]}},
            {"mine_details.district": blank_like},
            {"mine_details.state": blank_like},
        ]
    }
    return list(coll.find(query).limit(limit))

def heuristic_extract_location(text: str) -> Tuple[str, str]:
    """Extracts district and state from text using regex and keyword patterns."""
    if not text:
        return "", ""

    low = text.lower()
    state_found = ""
    for st in INDIAN_STATES:
        if f" {st} " in f" {low} ":
            state_found = st.title()
            break

    if not state_found:
        m_state = re.search(r"state\s*[:\-]\s*([A-Za-z .'-]{3,})", text, re.IGNORECASE)
        if m_state:
            cand = m_state.group(1).strip().lower()
            state_found = STATE_ABBREV.get(cand, cand.title())

    district_found = ""
    patterns = [
        r"([A-Za-z][A-Za-z .'-]{2,})\s+(?:district|dist\.|dst\.)",
        r"district\s+of\s+([A-Za-z][A-Za-z .'-]{2,})",
        r"district\s*[:\-]\s*([A-Za-z .'-]{3,})",
        r"in\s+([A-Za-z .'-]{3,})\s+district",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            district_found = m.group(1).strip().title()
            break

    if not district_found:
        for st in INDIAN_STATES:
            pat = re.compile(rf"([A-Za-z][A-Za-z .'-]{{2,}})\s*,\s*{re.escape(st)}", re.IGNORECASE)
            m = pat.search(text)
            if m:
                district_found = m.group(1).strip().title()
                if not state_found:
                    state_found = st.title()
                break

    return district_found, state_found

def guess_state_from_district(district: str) -> str:
    """Infers state from a known district."""
    if not district:
        return ""
    return DISTRICT_TO_STATE.get(district.strip().lower(), "")

def enrich_one(coll, doc: dict, dry_run: bool = False, verbose: bool = False) -> bool:
    """Enriches a single document from its stored text fields."""
    mine_name = (doc.get("mine_details", {}).get("name") or "").strip()
    
    # Combine all available text sources
    raw_text = doc.get("_raw_text", "") or ""
    loc_text = (doc.get("incident_details", {}).get("location", "") or "")
    combined_text = f"{loc_text}\n{raw_text}"

    dist, state = heuristic_extract_location(combined_text)

    if verbose:
        print(f"Report {doc.get('report_id','<no-id>')}: processing '{mine_name}'")
        if dist or state:
            print(f"  → Found from stored text: district='{dist}', state='{state}'")

    # Infer state from district if missing
    if not state and dist:
        inferred_state = guess_state_from_district(dist)
        if inferred_state:
            state = inferred_state
            if verbose:
                print(f"  → Inferred state from district: '{state}'")

    # Update only if new information was found
    current_dist = doc.get("mine_details", {}).get("district", "") or ""
    current_state = doc.get("mine_details", {}).get("state", "") or ""
    
    should_update = (dist and not current_dist) or (state and not current_state)
    if not should_update:
        if verbose:
            print("  → No new information to update.")
        return False

    update = {
        "mine_details.district": dist or current_dist,
        "mine_details.state": state or current_state,
        "_enriched_location_source": "heuristic_parser",
    }

    if dry_run:
        print(f"  → DRY RUN: Would update with: {update}")
        return True

    try:
        coll.update_one({"_id": doc["_id"]}, {"$set": update})
        print(f"  → Updated {doc.get('report_id', str(doc.get('_id')))}: district='{update['mine_details.district']}', state='{update['mine_details.state']}'")
        return True
    except Exception as e:
        print(f"  → Mongo update failed: {e}")
        return False

def enrich_all_locations():
    limit = int(os.environ.get("ENRICH_LIMIT", "40"))
    dry_run = os.environ.get("ENRICH_DRY_RUN", "false").lower() in ("1", "true", "yes")
    verbose = os.environ.get("ENRICH_VERBOSE", "false").lower() in ("1", "true", "yes")
    
    coll = mongo_collection()
    docs = find_missing_docs(coll, limit)
    
    if not docs:
        print("No documents with missing district/state found.")
        return
        
    print(f"Found {len(docs)} documents to enrich.")
    updated_count = 0
    for doc in docs:
        if enrich_one(coll, doc, dry_run=dry_run, verbose=verbose):
            updated_count += 1
            
    print(f"Done. Updated {updated_count}/{len(docs)} documents.")

def main():
    enrich_all_locations()

if __name__ == "__main__":
    main()

