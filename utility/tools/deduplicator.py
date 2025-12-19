from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from utility.config import MONGODB_DB, MONGODB_COLLECTION
from utility.db import get_mongo_client
from utility.tools.base import Tool

class DeduplicatorTool(Tool):
    """Tool for checking if a similar incident already exists in the database."""
    
    def __init__(self):
        super().__init__("deduplicator")
        self.client = get_mongo_client()
        self.coll = self.client[MONGODB_DB][MONGODB_COLLECTION]

    async def run(self, incident: Dict[str, Any]) -> bool:
        self.log_info(f"Checking for existing incident in DB: {incident.get('mine_name', 'N/A')} on {incident.get('incident_date', 'N/A')}")
        
        query = {}
        location_fields = ["state", "district"]
        for field in location_fields:
            if incident.get(field):
                query[f"mine_details.{field}"] = {"$regex": incident[field], "$options": "i"}

        if incident.get("mine_name"):
            query["mine_details.name"] = {"$regex": incident["mine_name"], "$options": "i"}

        incident_date_str = incident.get("incident_date")
        if incident_date_str:
            try:
                incident_date = datetime.strptime(incident_date_str, "%Y-%m-%d")
                start_date = incident_date - timedelta(days=3)
                end_date = incident_date + timedelta(days=3)
                query["accident_date"] = {
                    "$gte": start_date.strftime("%Y-%m-%d"),
                    "$lte": end_date.strftime("%Y-%m-%d")
                }
            except (ValueError, TypeError) as e:
                self.log_error(f"Invalid incident date format: {incident_date_str}", error=e)

        if not query:
            return False

        count = self.coll.count_documents(query)
        if count > 0:
            self.log_info(f"Found {count} similar incidents in the database.")
            return True
        else:
            self.log_info("No similar incidents found.")
            return False
