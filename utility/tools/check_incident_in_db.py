
from pymongo import MongoClient
from datetime import datetime, timedelta
from utility.config import MONGODB_URI, MONGODB_DB, MONGODB_COLLECTION

class CheckIncidentInDBTool:
    def __init__(self):
        self.name = "check_incident_in_db"
        self.description = "Checks if a similar incident already exists in the database."
        self.client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=4000)
        self.coll = self.client[MONGODB_DB][MONGODB_COLLECTION]

    def use(self, incident: dict) -> bool:
        print(f"Checking for existing incident in DB: {incident.get("mine_name", "N/A")} on {incident.get("incident_date", "N/A")}")
        
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
            except (ValueError, TypeError):
                print(f"Invalid incident date format: {incident_date_str}. Skipping date-based search.")

        if not query: # If no searchable fields are available
            return False

        count = self.coll.count_documents(query)
        if count > 0:
            print(f"Found {count} similar incidents in the database.")
            return True
        else:
            print("No similar incidents found.")
            return False
