
from utility.db import ensure_mongo_collection
from bson.objectid import ObjectId
from datetime import datetime, timezone
from web_news import fetch_article_text

class VerifyReportWithNewsTool:
    def __init__(self):
        self.name = "verify_report_with_news"
        self.description = "Verifies a report with news articles from the web."

    def use(self, report: dict, google_web_search_func) -> dict:
        print(f"Using verify_report_with_news tool for report: {report.get("report_id", "N/A")}")
        coll = ensure_mongo_collection()
        if coll is None:
            return {"status": "error", "message": "MongoDB not available."}

        # Extract key information from the report
        accident_date = report.get("accident_date")
        mine_details = report.get("mine_details", {})
        district = mine_details.get("district")
        state = mine_details.get("state")
        mine_name = mine_details.get("name")

        if not accident_date or not district or not state or not mine_name:
            print("Report is missing key information (date, district, state, or mine name) for verification.")
            return {"status": "error", "message": "Missing key information for verification."}

        # Construct more flexible search queries
        queries = [
            f'"{mine_name}" mine accident {district}',
            f'"{mine_name}" mine accident {state}',
            f'mine accident in {district}, {state} on {accident_date[:10]}'
        ]

        corroborating_articles = []
        for query in queries:
            print(f"Searching Google with query: {query}")
            search_results = google_web_search_func(query)

            if search_results and search_results.get("results"):
                for result in search_results["results"]:
                    article_url = result.get("url")
                    if not article_url or article_url in corroborating_articles:
                        continue

                    # Fetch full article text
                    article_text = fetch_article_text(article_url)
                    if not article_text:
                        continue

                    # More flexible keyword matching on full text
                    text_lower = article_text.lower()
                    mine_name_present = mine_name.lower() in text_lower
                    district_present = district.lower() in text_lower
                    state_present = state.lower() in text_lower

                    if mine_name_present and (district_present or state_present):
                        corroborating_articles.append(article_url)
                        print(f"Found corroborating article: {article_url}")

            if len(corroborating_articles) >= 3: # Stop if we have enough evidence
                break

        # Determine verification status
        if corroborating_articles:
            status = "verified"
            print(f"Report {report.get("report_id", "N/A")} verified with {len(corroborating_articles)} articles.")
        else:
            status = "unverified"
            print(f"Report {report.get("report_id", "N/A")} could not be verified.")
        
        return {"status": status, "articles": corroborating_articles}
