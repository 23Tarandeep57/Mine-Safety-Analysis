
from utility.db import ensure_mongo_collection
from web_news import analyze_common_patterns

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
        # For now, we'll just fetch the summary and title, similar to how web_news expects it.
        # In a more advanced scenario, we might fetch more structured data.
        incidents = list(self.coll.find({}, {"summary": 1, "_raw_title": 1, "_id": 0}))

        if not incidents:
            return "No incidents found in the database for analysis."

        # Convert to the format expected by analyze_common_patterns
        articles_for_analysis = []
        for inc in incidents:
            if inc.get("summary") and inc.get("_raw_title"):
                articles_for_analysis.append({"summary": inc["summary"], "title": inc["_raw_title"]})

        if not articles_for_analysis:
            return "No suitable incident summaries found for analysis."

        analysis_report = analyze_common_patterns(articles_for_analysis)
        print("Incident pattern analysis complete.")
        return analysis_report
