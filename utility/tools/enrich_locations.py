from enrich_locations import enrich_all_locations

class EnrichLocationsTool:
    def __init__(self):
        self.name = "enrich_locations"
        self.description = "Enriches the location data of the reports in the database."

    def use(self):
        print("Using enrich_locations tool...")
        enrich_all_locations()
