from analyze_reports import analyze_all_reports

class AnalyzeReportsTool:
    def __init__(self):
        self.name = "analyze_reports"
        self.description = "Analyzes all the reports in the database and generates a report."

    def use(self):
        print("Using analyze_reports tool...")
        analyze_all_reports()
