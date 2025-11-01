
from scrape_reports import process_link
from utility.db import ensure_mongo_collection

class CollectDGMSReportTool:
    def __init__(self):
        self.name = "collect_dgms_report"
        self.description = "Collects and parses a full DGMS report from a given link."

    def use(self, report_link: dict) -> dict:
        print(f"Collecting full DGMS report from: {report_link["url"]}")
        coll = ensure_mongo_collection()
        if coll is None:
            return {"status": "error", "message": "MongoDB not available."}
        
        doc = process_link(report_link, coll)
        return {"status": "success", "document": doc}
