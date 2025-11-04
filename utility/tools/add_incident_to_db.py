from pymongo import MongoClient
from datetime import datetime, timezone
from utility.config import MONGODB_URI, MONGODB_DB, MONGODB_COLLECTION
from schemas import Report, MineDetails, IncidentDetails, Verification
from utility.tools.find_cause_code import FindCauseCodeTool
from utility.local_search import google_web_search
import re


class AddIncidentToDBTool:
    """
    Tool for adding a new incident record to the MongoDB database.
    It also enriches missing mine details (district, state) via Google search if needed.
    """

    def __init__(self):
        self.name = "add_incident_to_db"
        self.description = "Adds a new incident to the database."
        self.client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=4000)
        self.coll = self.client[MONGODB_DB][MONGODB_COLLECTION]

    def use(self, incident: dict, source_url: str, raw_title: str) -> dict:
        """Add a new incident entry into MongoDB."""
        print(f"Adding incident to DB: {incident.get('mine_name', 'N/A')} on {incident.get('incident_date', 'N/A')}")

        # Enrich missing mine data if needed
        incident = self.enrich_missing_data(incident)

        # Ensure cause_code is computed from brief_cause if not provided
        if not incident.get("cause_code") and incident.get("brief_cause"):
            try:
                finder = FindCauseCodeTool()
                code = finder.use(incident.get("brief_cause", ""))
                if code:
                    incident["cause_code"] = code
            except Exception as e:
                print(f"Warning: could not compute cause_code: {e}")

        try:
            report = Report(
                mine_details=MineDetails(
                    name=incident.get("mine_name"),
                    district=incident.get("district"),
                    state=incident.get("state"),
                ),
                incident_details=IncidentDetails(
                    fatalities=[{}] * (incident.get("fatalities") or 0),
                    injuries=[{}] * (incident.get("injuries") or 0),
                    brief_cause=incident.get("brief_cause"),
                    cause_code=incident.get("cause_code"),
                ),
                accident_date=incident.get("incident_date"),
                source_url=source_url,
                _raw_title=raw_title,
                _raw_text=incident.get("brief_cause"),
                verification=Verification(
                    status="unverified_news_report",
                    timestamp=datetime.now(timezone.utc),
                    articles=[source_url],
                ),
            )

            doc = report.model_dump(by_alias=True)
            result = self.coll.insert_one(doc)

            print(f"Incident added to DB with _id: {result.inserted_id}")
            return {"status": "success", "_id": str(result.inserted_id)}

        except Exception as e:
            print(f"Error adding incident to DB: {e}")
            return {"status": "error", "message": str(e)}

    def enrich_missing_data(self, incident: dict) -> dict:
        """
        Enrich incident details with district and state if missing,
        using a simple Google search-based heuristic.
        """
        mine_name = incident.get("mine_name")
        district = incident.get("district")
        state = incident.get("state")

        # Skip if no mine name or already has location info
        if not mine_name or (district and state):
            return incident

        print(f"Enriching missing data for {mine_name}...")
        query = f"{mine_name} location"
        search_results = google_web_search(query)

        if not search_results:
            return incident

        for result in search_results:
            snippet = result.get("snippet", "")
            # Simple regex pattern to extract district and state
            match = re.search(r"(.*?),\s*(.*?),\s*India", snippet)
            if match:
                found_district = match.group(1)
                found_state = match.group(2)
                incident["district"] = found_district
                incident["state"] = found_state
                print(f"Found missing data: District - {found_district}, State - {found_state}")
                return incident

        return incident
