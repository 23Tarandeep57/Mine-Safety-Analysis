
from utility.db import ensure_mongo_collection
from bson.objectid import ObjectId
from datetime import datetime, timezone

class VerifyReportWithNewsTool:
    def __init__(self, agent):
        self.name = "verify_report_with_news"
        self.description = "Verifies a report with news articles from the web."
        self.agent = agent

    def use(self, report_id):
        print(f"Using verify_report_with_news tool for report: {report_id}")
        coll = ensure_mongo_collection()
        if coll is None:
            print("MongoDB not available. Cannot verify report.")
            return

        report = coll.find_one({"report_id": report_id})
        if not report:
            print(f"Report with id {report_id} not found in the database.")
            return

        # Extract key information from the report
        accident_date = report.get("accident_date")
        mine_details = report.get("mine_details", {})
        district = mine_details.get("district")
        state = mine_details.get("state")
        mine_name = mine_details.get("name")

        if not accident_date or not district or not state:
            print("Report is missing key information (date, district, or state) for verification.")
            self.update_verification_status(coll, report["_id"], "error", [])
            return

        # Construct search query
        query = f'"{mine_name}" mine accident in {district}, {state} on {accident_date[:10]}'
        print(f"Searching Google with query: {query}")

        # Use the google_web_search tool
        search_results = self.agent.google_web_search(query)

        # Analyze search results
        corroborating_articles = []
        if search_results and search_results.get("results"):
            for result in search_results["results"]:
                # Simple keyword matching
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                if mine_name.lower() in title.lower() or mine_name.lower() in snippet.lower():
                    if district.lower() in title.lower() or district.lower() in snippet.lower():
                        if state.lower() in title.lower() or state.lower() in snippet.lower():
                            corroborating_articles.append(result.get("link"))

        # Update the report with the verification status
        if corroborating_articles:
            self.update_verification_status(coll, report["_id"], "verified", corroborating_articles)
            print(f"Report {report_id} verified with {len(corroborating_articles)} articles.")
        else:
            self.update_verification_status(coll, report["_id"], "unverified", [])
            print(f"Report {report_id} could not be verified.")

    def update_verification_status(self, coll, report_oid, status, articles):
        coll.update_one(
            {"_id": report_oid},
            {
                "$set": {
                    "verification": {
                        "status": status,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "articles": articles,
                    }
                }
            }
        )
