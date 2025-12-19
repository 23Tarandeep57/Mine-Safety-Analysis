import re
from typing import Any, Dict, Optional, Tuple
from utility.tools.base import Tool
from utility.tools.find_cause_code import FindCauseCodeTool
from utility.local_search import google_web_search

# --- Heuristics Data (from enrich_locations.py) ---

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


def heuristic_extract_location(text: str) -> Tuple[str, str]:
    """Extracts district and state from text using regex and keyword patterns."""
    if not text:
        return "", ""

    low = text.lower()
    state_found = ""

    # 1. Direct state name match
    for st in INDIAN_STATES:
        if f" {st} " in f" {low} ":
            state_found = st.title()
            break

    # 2. State abbreviation match
    if not state_found:
        m_state = re.search(r"state\s*[:\-]\s*([A-Za-z .'-]{3,})", text, re.IGNORECASE)
        if m_state:
            cand = m_state.group(1).strip().lower()
            state_found = STATE_ABBREV.get(cand, cand.title())

    # 3. District extraction
    district_found = ""
    patterns = [
        r"([A-Za-z][A-Za-z .'-]{2,})\s+(?:district|dist\.|dst\.)",
        r"district\s+of\s+([A-Za-z][A-Za-z .'-]{2,})",
        r"district\s*[:\-]\s*([A-Za-z .'-]{3,})",
        r"in\s+([A-Za-z .'-]{3,})\s+district",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            district_found = m.group(1).strip().title()
            break

    # 4. If we found district but no state, try to infer state from district
    if district_found and not state_found:
        state_found = DISTRICT_TO_STATE.get(district_found.lower(), "")

    return district_found, state_found


class EnricherTool(Tool):
    """Tool for enriching incident data with location and cause codes."""
    
    def __init__(self):
        super().__init__("enricher")
        self.cause_finder = FindCauseCodeTool()

    async def run(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        self.log_info(f"Enriching incident: {incident.get('mine_name', 'N/A')}")
        
        # 1. Enrich missing location data
        incident = await self._enrich_location(incident)
        
        # 2. Enrich cause code if missing
        if not incident.get("cause_code") and incident.get("brief_cause"):
            try:
                code = self.cause_finder.use(incident.get("brief_cause", ""))
                if code:
                    incident["cause_code"] = code
                    self.log_info(f"Found cause code: {code}")
            except Exception as e:
                self.log_error("Failed to find cause code", error=e)
                
        return incident

    async def _enrich_location(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        mine_name = incident.get("mine_name", "")
        district = incident.get("district", "")
        state = incident.get("state", "")
        brief_cause = incident.get("brief_cause", "")

        # Already have both, skip enrichment
        if district and state:
            return incident

        # --- Step 1: Try heuristic extraction from existing text ---
        combined_text = f"{mine_name} {brief_cause} {incident.get('summary', '')}"
        heuristic_district, heuristic_state = heuristic_extract_location(combined_text)

        if heuristic_district and not district:
            incident["district"] = heuristic_district
            self.log_info(f"Heuristic found district: {heuristic_district}")
        if heuristic_state and not state:
            incident["state"] = heuristic_state
            self.log_info(f"Heuristic found state: {heuristic_state}")

        # If we now have both, return
        if incident.get("district") and incident.get("state"):
            return incident

        # --- Step 2: Fallback to web search if still missing ---
        if mine_name and (not incident.get("district") or not incident.get("state")):
            self.log_info(f"Falling back to web search for {mine_name}")
            try:
                query = f"{mine_name} mine location district state India"
                search_results = google_web_search(query)

                if search_results:
                    for result in search_results:
                        snippet = result.get("snippet", "")
                        web_district, web_state = heuristic_extract_location(snippet)
                        if web_district and not incident.get("district"):
                            incident["district"] = web_district
                        if web_state and not incident.get("state"):
                            incident["state"] = web_state
                        if incident.get("district") and incident.get("state"):
                            self.log_info(f"Web search found: {incident['district']}, {incident['state']}")
                            break
            except Exception as e:
                self.log_error(f"Web search failed: {e}")

        return incident
