
from pymongo import MongoClient
from datetime import datetime, timezone
from utility.config import MONGODB_URI, MONGODB_DB, MONGODB_COLLECTION
from schemas import Report, MineDetails, IncidentDetails, Verification

class AddIncidentToDBTool:
    def __init__(self):
        self.name = "add_incident_to_db"
        self.description = "Adds a new incident to the database."
        self.client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=4000)
        self.coll = self.client[MONGODB_DB][MONGODB_COLLECTION]

    def use(self, incident: dict, source_url: str, raw_title: str) -> dict:
        print(f"Adding incident to DB: {incident.get("mine_name", "N/A")} on {incident.get("incident_date", "N/A")}")
        
        try:
            report = Report(
                mine_details=MineDetails(
                    name=incident.get("mine_name"),
                    district=incident.get("district"),
                    state=incident.get("state"),
                ),
                incident_details=IncidentDetails(
                    fatalities=[{}] * incident.get("fatalities", 0),
                    injuries=[{}] * incident.get("injuries", 0),
                    brief_cause=incident.get("brief_cause"),
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
