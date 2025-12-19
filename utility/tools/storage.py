from datetime import datetime, timezone
from typing import Any, Dict, Optional
from utility.config import MONGODB_DB, MONGODB_COLLECTION
from utility.db import get_mongo_client
from utility.tools.base import Tool
from schemas import Report, MineDetails, IncidentDetails, Verification

class StorageTool(Tool):
    """Tool for persisting incident records to MongoDB."""
    
    def __init__(self):
        super().__init__("storage")
        self.client = get_mongo_client()
        self.coll = self.client[MONGODB_DB][MONGODB_COLLECTION]

    async def run(self, incident: Dict[str, Any], source_url: str, raw_title: str) -> Dict[str, Any]:
        self.log_info(f"Storing incident in DB: {incident.get('mine_name', 'N/A')}")
        
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

            self.log_info(f"Incident stored with _id: {result.inserted_id}")
            return {"status": "success", "_id": str(result.inserted_id)}

        except Exception as e:
            self.log_error("Error storing incident in DB", error=e)
            return {"status": "error", "message": str(e)}
