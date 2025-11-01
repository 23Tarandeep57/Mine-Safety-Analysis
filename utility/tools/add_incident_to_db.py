
from pymongo import MongoClient
from datetime import datetime, timezone
from utility.config import MONGODB_URI, MONGODB_DB, MONGODB_COLLECTION

class AddIncidentToDBTool:
    def __init__(self):
        self.name = "add_incident_to_db"
        self.description = "Adds a new incident to the database."
        self.client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=4000)
        self.coll = self.client[MONGODB_DB][MONGODB_COLLECTION]

    def use(self, incident: dict, source_url: str, raw_title: str) -> dict:
        print(f"Adding incident to DB: {incident.get("mine_name", "N/A")} on {incident.get("incident_date", "N/A")}")
        
        doc = {
            "report_id": None, # No DGMS report ID yet
            "date_reported": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "accident_date": incident.get("incident_date"),
            "mine_details": {
                "name": incident.get("mine_name"),
                "district": incident.get("district"),
                "state": incident.get("state"),
                "mineral": None, # Not available from news for now
            },
            "incident_details": {
                "location": None, # Not available from news for now
                "fatalities": [{
                    "name": None,
                    "designation": None,
                    "age": None,
                    "experience": None
                }] if incident.get("fatalities") else [],
                "injuries": [] if incident.get("injuries") else [],
                "brief_cause": incident.get("brief_cause"),
            },
            "best_practices": [],
            "source_url": source_url,
            "summary": incident.get("brief_cause"), # Use brief cause as summary for now
            "created_at": datetime.now(timezone.utc).isoformat(),
            "verification": {
                "status": "unverified_news_report",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "articles": [source_url],
            },
            "_raw_title": raw_title,
            "_raw_text": incident.get("brief_cause"), # Use brief cause as raw text for now
        }

        # Update fatalities and injuries count if available
        if incident.get("fatalities") is not None:
            doc["incident_details"]["fatalities"] = [{"count": incident["fatalities"]}]
        if incident.get("injuries") is not None:
            doc["incident_details"]["injuries"] = [{"count": incident["injuries"]}]

        try:
            result = self.coll.insert_one(doc)
            print(f"Incident added to DB with _id: {result.inserted_id}")
            return {"status": "success", "_id": str(result.inserted_id)}
        except Exception as e:
            print(f"Error adding incident to DB: {e}")
            return {"status": "error", "message": str(e)}
