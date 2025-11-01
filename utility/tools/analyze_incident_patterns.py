
from utility.db import ensure_mongo_collection
from utility.analysis import make_advanced_report, render_narrative

class AnalyzeIncidentPatternsTool:
    def __init__(self):
        self.name = "analyze_incident_patterns"
        self.description = "Analyzes all incidents in the database to identify common patterns and themes."
        self.coll = ensure_mongo_collection()

    def use(self) -> str:
        print("Analyzing incident patterns...")
        if self.coll is None:
            return "Error: MongoDB not available."

        # Fetch all incidents from the database
        incidents = list(self.coll.find({}))

        if not incidents:
            return "No incidents found in the database for analysis."

        # Use make_advanced_report and render_narrative for structured analysis
        # Default parameters for make_advanced_report can be configured or passed as arguments
        advanced_report_data = make_advanced_report(incidents)
        analysis_report = render_narrative(advanced_report_data)
        
        print("Incident pattern analysis complete.")
        return analysis_report
