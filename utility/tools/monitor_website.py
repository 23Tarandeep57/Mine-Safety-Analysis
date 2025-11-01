
from utility.scraper import scrape_fatal_reports
from utility.db import ensure_mongo_collection
from utility.parser import _derive_report_id
from utility.extract import extract_text_from_url
from utility.task import Task

class MonitorWebsiteTool:
    def __init__(self, agent):
        self.name = "monitor_website"
        self.description = "Monitors the DGMS website for new reports."
        self.agent = agent

    def use(self):
        print("Using monitor_website tool...")
        coll = ensure_mongo_collection()
        if coll is None:
            print("MongoDB not available. Cannot monitor website.")
            return

        try:
            links = scrape_fatal_reports()
        except Exception as e:
            print(f"Failed to scrape base page: {e}")
            return

        if not links:
            print("No fatal accident report links found.")
            return

        for link in links:
            report_id = self.get_report_id_from_link(link)

            if report_id and not self.is_report_in_db(coll, report_id):
                print(f"New report found: {report_id}")
                self.agent.add_task(Task("collect_reports", {"link": link}))
                self.agent.add_task(Task("verify_report_with_news", {"report_id": report_id}))

    def get_report_id_from_link(self, link):
        # Fetch the first 4096 bytes of the report to get the report id
        text = extract_text_from_url(link["url"], max_bytes=4096)
        return _derive_report_id(text, link["title"])

    def is_report_in_db(self, coll, report_id):
        return coll.count_documents({"report_id": report_id}) > 0
