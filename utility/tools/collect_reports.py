from scrape_reports import collect_all_reports, process_link
from utility.db import ensure_mongo_collection

class CollectReportsTool:
    def __init__(self):
        self.name = "collect_reports"
        self.description = "Collects all the fatal accident reports from the DGMS website, or a single report if a link is provided."

    def use(self, link=None):
        print("Using collect_reports tool...")
        if link:
            coll = ensure_mongo_collection()
            process_link(link, coll)
        else:
            collect_all_reports()
