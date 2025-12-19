import re
from typing import Any, Dict, Optional
from utility.tools.base import Tool
from utility.tools.find_cause_code import FindCauseCodeTool
from utility.local_search import google_web_search

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
        mine_name = incident.get("mine_name")
        district = incident.get("district")
        state = incident.get("state")

        if not mine_name or (district and state):
            return incident

        self.log_info(f"Searching for missing location data for {mine_name}")
        query = f"{mine_name} location"
        search_results = google_web_search(query)

        if not search_results:
            return incident

        for result in search_results:
            snippet = result.get("snippet", "")
            match = re.search(r"(.*?),\s*(.*?),\s*India", snippet)
            if match:
                incident["district"] = match.group(1)
                incident["state"] = match.group(2)
                self.log_info(f"Found location: {incident['district']}, {incident['state']}")
                break
                
        return incident
