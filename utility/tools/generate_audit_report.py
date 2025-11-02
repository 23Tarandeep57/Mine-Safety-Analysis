
import os
from datetime import datetime, timedelta
from utility.db import ensure_mongo_collection
from utility.tools.analyze_incident_patterns import AnalyzeIncidentPatternsTool
from utility.tools.generate_safety_alerts import GenerateSafetyAlertsTool
from utility.tools.generate_recommendations import GenerateRecommendationsTool
from utility.config import DATA_DIR

class GenerateAuditReportTool:
    def __init__(self):
        self.name = "generate_audit_report"
        self.description = "Generates a safety audit report based on the incidents in the database."
        self.coll = ensure_mongo_collection()
        self.analyze_patterns_tool = AnalyzeIncidentPatternsTool()
        self.generate_alerts_tool = GenerateSafetyAlertsTool()
        self.generate_recommendations_tool = GenerateRecommendationsTool()

    def use(self, days_back: int = 365) -> str:
        print(f"Generating safety audit report for the last {days_back} days...")
        if self.coll is None:
            return "Error: MongoDB not available."

        # --- 1. Gather Data ---
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        query = {
            "accident_date": {
                "$gte": start_date.strftime("%Y-%m-%d"),
                "$lte": end_date.strftime("%Y-%m-%d")
            }
        }
        incidents = list(self.coll.find(query))
        num_incidents = len(incidents)
        # Note: This is a simplified fatality/injury count
        num_fatalities = sum(len(i.get("incident_details", {}).get("fatalities", [])) for i in incidents)
        num_injuries = sum(len(i.get("incident_details", {}).get("injuries", [])) for i in incidents)

        # --- 2. Incorporate AI Analysis ---
        analysis_report_text = self.analyze_patterns_tool.use()
        alerts = self.generate_alerts_tool.use(analysis_report_text)
        recommendations = self.generate_recommendations_tool.use(analysis_report_text)

        # --- 3. Generate the Report ---
        report_content = self._build_markdown_report(
            start_date, end_date, num_incidents, num_fatalities, num_injuries, 
            analysis_report_text, alerts, recommendations
        )

        # --- 4. Save the Report ---
        report_filename = f"safety_audit_report_{end_date.strftime('%Y%m%d')}.md"
        report_path = DATA_DIR / report_filename
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_content)
            print(f"Successfully generated audit report: {report_path}")
            return f"Report generated at {report_path}"
        except Exception as e:
            print(f"Error saving report: {e}")
            return f"Error saving report: {e}"

    def _build_markdown_report(self, start_date, end_date, num_incidents, num_fatalities, num_injuries, analysis, alerts, recommendations):
        report = f"""# Mine Safety Audit Report

**Report Date:** {datetime.now().strftime("%Y-%m-%d")}

**Time Period:** {start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")}

---

## 1. Executive Summary

This report provides an automated analysis of mine safety incidents based on data collected from DGMS and news sources. During this period, **{num_incidents}** incidents were recorded, resulting in **{num_fatalities}** fatalities and **{num_injuries}** injuries. Key patterns and safety alerts have been automatically generated to highlight areas requiring attention.

---

## 2. Incident Statistics

- **Total Incidents:** {num_incidents}
- **Total Fatalities:** {num_fatalities}
- **Total Injuries:** {num_injuries}

---

## 3. AI-Powered Pattern Analysis

The following common patterns and recurring themes were identified from the incident data:

{analysis}

---

## 4. Generated Safety Alerts

Based on the pattern analysis, the following actionable safety alerts have been generated:

"""
        for alert in alerts:
            report += f"- **ALERT:** {alert}\n"
        
        report += "\n---\n\n## 5. Recommendations\n\n"

        for rec in recommendations:
            report += f"- {rec}\n"

        return report
