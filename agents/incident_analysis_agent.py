
import asyncio
from typing import Literal
from utility.agent_framework import Agent
from utility.tools.extract_incident_from_news import ExtractIncidentFromNewsTool
from utility.tools.check_incident_in_db import CheckIncidentInDBTool
from utility.tools.add_incident_to_db import AddIncidentToDBTool
from utility.tools.collect_dgms_report import CollectDGMSReportTool
from utility.tools.verify_report_with_news import VerifyReportWithNewsTool
from utility.tools.analyze_incident_patterns import AnalyzeIncidentPatternsTool
from utility.tools.generate_safety_alerts import GenerateSafetyAlertsTool

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
import operator
from datetime import datetime, timezone

# Define the state for LangGraph
class IncidentAnalysisState(TypedDict):
    # For news articles
    article: dict  # The news article being processed
    extracted_incident: dict  # Structured data extracted from the article
    is_duplicate: bool  # Whether a similar incident exists in DB
    db_add_result: dict  # Result of adding to DB

    # For DGMS reports
    dgms_report_link: dict # The DGMS report link (from DGMSMonitorAgent)
    dgms_document: dict # The full DGMS document collected
    verification_result: dict # Result of news verification

# Define the IncidentAnalysisAgent
class IncidentAnalysisAgent(Agent):
    def __init__(self, name, message_bus, google_web_search_func):
        super().__init__(name, message_bus)
        self.google_web_search = google_web_search_func
        self.extract_tool = ExtractIncidentFromNewsTool()
        self.check_db_tool = CheckIncidentInDBTool()
        self.add_db_tool = AddIncidentToDBTool()
        self.collect_dgms_tool = CollectDGMSReportTool()
        self.verify_tool = VerifyReportWithNewsTool()
        self.analyze_patterns_tool = AnalyzeIncidentPatternsTool()
        self.generate_alerts_tool = GenerateSafetyAlertsTool()
        self.news_article_graph = self._build_news_article_graph()
        self.dgms_report_graph = self._build_dgms_report_graph()
        self.subscribe("new_news_article", self.handle_news_article)
        self.subscribe("new_dgms_report", self.handle_dgms_report)

    def _build_news_article_graph(self):
        workflow = StateGraph(IncidentAnalysisState)
        workflow.add_node("extract_incident", self.extract_incident_node)
        workflow.add_node("check_duplicate", self.check_duplicate_node)
        workflow.add_node("add_to_db", self.add_to_db_node)
        workflow.set_entry_point("extract_incident")
        workflow.add_edge("extract_incident", "check_duplicate")
        workflow.add_conditional_edges(
            "check_duplicate",
            self.route_duplicate_check,
            {
                "duplicate": END,
                "not_duplicate": "add_to_db",
            },
        )
        workflow.add_edge("add_to_db", END)
        return workflow.compile()

    def _build_dgms_report_graph(self):
        workflow = StateGraph(IncidentAnalysisState)
        workflow.add_node("collect_dgms", self.collect_dgms_node)
        workflow.add_node("verify_dgms", self.verify_dgms_node)
        workflow.add_node("update_dgms_db", self.update_dgms_db_node)
        workflow.set_entry_point("collect_dgms")
        workflow.add_edge("collect_dgms", "verify_dgms")
        workflow.add_edge("verify_dgms", "update_dgms_db")
        workflow.add_edge("update_dgms_db", END)
        return workflow.compile()

    async def extract_incident_node(self, state: IncidentAnalysisState) -> dict:
        print(f"[{self.name}] Extracting incident from article...")
        extracted_data = self.extract_tool.use(state["article"])
        return {"extracted_incident": extracted_data}

    async def check_duplicate_node(self, state: IncidentAnalysisState) -> dict:
        print(f"[{self.name}] Checking for duplicate incident...")
        is_duplicate = self.check_db_tool.use(state["extracted_incident"])
        return {"is_duplicate": is_duplicate}

    async def add_to_db_node(self, state: IncidentAnalysisState) -> dict:
        print(f"[{self.name}] Adding new incident to DB...")
        article = state["article"]
        db_add_result = self.add_db_tool.use(
            state["extracted_incident"],
            article["url"],
            article["title"],
        )
        return {"db_add_result": db_add_result}

    async def collect_dgms_node(self, state: IncidentAnalysisState) -> dict:
        print(f"[{self.name}] Collecting full DGMS report...")
        result = self.collect_dgms_tool.use(state["dgms_report_link"]["link"])
        if result["status"] == "success":
            return {"dgms_document": result["document"]}
        else:
            print(f"Error collecting DGMS report: {result["message"]}")
            return {"dgms_document": None} # Or handle error state

    async def verify_dgms_node(self, state: IncidentAnalysisState) -> dict:
        print(f"[{self.name}] Verifying DGMS report with news...")
        if state["dgms_document"] is None:
            return {"verification_result": {"status": "error", "message": "No DGMS document to verify."}}
        
        verification_result = self.verify_tool.use(state["dgms_document"], self.google_web_search)
        return {"verification_result": verification_result}

    async def update_dgms_db_node(self, state: IncidentAnalysisState) -> dict:
        print(f"[{self.name}] Updating DGMS report in DB with verification status...")
        if state["dgms_document"] is None or state["verification_result"] is None:
            print("Cannot update DGMS DB: missing document or verification result.")
            return {}

        coll = self.add_db_tool.coll # Re-use the collection from add_db_tool
        report_id = state["dgms_document"].get("report_id")
        if not report_id:
            print("Cannot update DGMS DB: report_id missing from document.")
            return {}

        update_data = {
            "verification": {
                "status": state["verification_result"]["status"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "articles": state["verification_result"].get("articles", []),
            }
        }
        try:
            coll.update_one({"report_id": report_id}, {"$set": update_data})
            print(f"DGMS report {report_id} updated with verification status: {update_data["verification"]["status"]}")
        except Exception as e:
            print(f"Error updating DGMS report {report_id} in DB: {e}")
        return {}

    def route_duplicate_check(self, state: IncidentAnalysisState) -> Literal["duplicate", "not_duplicate"]:
        if state["is_duplicate"]:
            print(f"[{self.name}] Incident is a duplicate, ending workflow.")
            return "duplicate"
        else:
            print(f"[{self.name}] Incident is not a duplicate, proceeding to add to DB.")
            return "not_duplicate"

    async def handle_news_article(self, message):
        print(f"[{self.name}] Received new news article: {message["payload"]["title"]}")
        initial_state = {"article": message["payload"]}
        await self.news_article_graph.ainvoke(initial_state, config={"recursion_limit": 50})

    async def handle_dgms_report(self, message):
        print(f"[{self.name}] Received new DGMS report link: {message["payload"]["report_id"]}")
        initial_state = {"dgms_report_link": message["payload"]}
        await self.dgms_report_graph.ainvoke(initial_state, config={"recursion_limit": 50})

    async def _run_periodic_analysis(self):
        while self.running:
            print(f"[{self.name}] Running periodic analysis...")
            analysis_report = self.analyze_patterns_tool.use()
            print(f"[{self.name}] Analysis Report: {analysis_report[:200]}...")
            if analysis_report and "Error" not in analysis_report:
                alerts = self.generate_alerts_tool.use(analysis_report)
                for alert in alerts:
                    print(f"[{self.name}] Generated Alert: {alert}")
                    await self.publish("safety_alert", {"alert_message": alert})
            await asyncio.sleep(3600) # Run analysis every hour

    async def run(self):
        asyncio.create_task(self._run_periodic_analysis())
        while self.running:
            await asyncio.sleep(1) # Keep agent alive
