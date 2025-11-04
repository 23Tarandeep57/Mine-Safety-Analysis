#!/usr/bin/env python3
import os
import re
from typing import Tuple, List
from pymongo import MongoClient
import certifi

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
    client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=4000,
        tlsCAFile=certifi.where(),
    )
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
