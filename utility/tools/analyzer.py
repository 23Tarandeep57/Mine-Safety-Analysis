from typing import Any, Dict, Optional
from utility.db import ensure_mongo_collection
from utility.analysis import make_advanced_report, render_narrative
from utility.tools.base import Tool

class AnalyzerTool(Tool):
    """Tool for analyzing incident patterns using advanced topic modeling."""
    
    def __init__(self):
        super().__init__("analyzer")
        self.coll = ensure_mongo_collection()

    async def run(self) -> str:
        self.log_info("Analyzing incident patterns...")
        if self.coll is None:
            self.log_error("MongoDB not available")
            return "Error: MongoDB not available."

        incidents = list(self.coll.find({}))
        if not incidents:
            self.log_info("No incidents found in the database for analysis.")
            return "No incidents found in the database for analysis."

        # make_advanced_report will eventually use BERTopic
        advanced_report_data = make_advanced_report(incidents)
        analysis_report = render_narrative(advanced_report_data)
        
        self.log_info("Incident pattern analysis complete.")
        return analysis_report
