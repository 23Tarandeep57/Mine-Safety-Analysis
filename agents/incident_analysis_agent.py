
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
from utility.tools.generate_audit_report import GenerateAuditReportTool
from utility.config import DATA_DIR
import json
import inspect
import traceback
import os

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
import operator
from datetime import datetime, timezone

from utility.chatbot_utils import get_standalone_question, retrieve_from_chroma, retrieve_from_mongodb, format_docs
from langchain_core.messages import HumanMessage, AIMessage

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
    news_scan_results: dict # Results from the NewsScannerAgent

# Define the IncidentAnalysisAgent
class IncidentAnalysisAgent(Agent):
    def __init__(self, name, message_bus, google_web_search_func, llm, vector_store, mongo_collection, contextualize_q_chain, qa_chain):
        super().__init__(name, message_bus)
        self.chat_history_lock = asyncio.Lock()
        self.google_web_search = google_web_search_func
        self.extract_tool = ExtractIncidentFromNewsTool()
        self.check_db_tool = CheckIncidentInDBTool()
        self.add_db_tool = AddIncidentToDBTool()
        self.collect_dgms_tool = CollectDGMSReportTool()
        self.verify_tool = VerifyReportWithNewsTool()
        self.analyze_patterns_tool = AnalyzeIncidentPatternsTool()
        self.generate_alerts_tool = GenerateSafetyAlertsTool()
        self.generate_audit_tool = GenerateAuditReportTool()
        self.news_article_graph = self._build_news_article_graph()
        self.dgms_report_graph = self._build_dgms_report_graph()
        self.subscribe("new_news_article", self.handle_news_article)
        self.subscribe("new_dgms_report", self.handle_dgms_report)
        self.subscribe("user_query", self.handle_user_query)
        self.subscribe("news_scan_results", self.handle_news_scan_results)

        # Chatbot components
        self.llm = llm
        self.vector_store = vector_store
        self.mongo_collection = mongo_collection
        self.contextualize_q_chain = contextualize_q_chain
        self.qa_chain = qa_chain
        self.chat_history = [] # Maintain chat history for contextualization

        # For agent collaboration
        self.news_scan_complete = asyncio.Event()

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
        workflow.add_node("request_news_scan", self.request_news_scan_node)
        workflow.add_node("wait_for_news_scan", self.wait_for_news_scan_node)
        workflow.add_node("update_dgms_db", self.update_dgms_db_node)
        workflow.set_entry_point("collect_dgms")
        workflow.add_edge("collect_dgms", "request_news_scan")
        workflow.add_edge("request_news_scan", "wait_for_news_scan")
        workflow.add_edge("wait_for_news_scan", "update_dgms_db")
        workflow.add_edge("update_dgms_db", END)
        return workflow.compile()

    async def extract_incident_node(self, state: IncidentAnalysisState) -> dict:
        print(f"[{self.name}] Extracting incident from article...")
        extracted_data = await asyncio.to_thread(self.extract_tool.use, state["article"])
        return {"extracted_incident": extracted_data}

    async def check_duplicate_node(self, state: IncidentAnalysisState) -> dict:
        print(f"[{self.name}] Checking for duplicate incident...")
        is_duplicate = await asyncio.to_thread(self.check_db_tool.use, state["extracted_incident"])
        return {"is_duplicate": is_duplicate}

    async def add_to_db_node(self, state: IncidentAnalysisState) -> dict:
        print(f"[{self.name}] Adding new incident to DB...")
        article = state["article"]
        db_add_result = await asyncio.to_thread(self.add_db_tool.use,
            state["extracted_incident"],
            article["url"],
            article["title"],
        )
        return {"db_add_result": db_add_result}

    async def collect_dgms_node(self, state: IncidentAnalysisState) -> dict:
        print(f"[{self.name}] Collecting full DGMS report...")
        result = await asyncio.to_thread(self.collect_dgms_tool.use, state["dgms_report_link"]["link"])
        if result["status"] == "success":
            return {"dgms_document": result["document"]}
        else:
            print(f"Error collecting DGMS report: {result["message"]}")
            return {"dgms_document": None} # Or handle error state

    async def request_news_scan_node(self, state: IncidentAnalysisState) -> dict:
        print(f"[{self.name}] Requesting news scan from NewsScannerAgent...")
        if state["dgms_document"]:
            incident_details = {
                "mine_name": state["dgms_document"].get("mine_details", {}).get("name"),
                "district": state["dgms_document"].get("mine_details", {}).get("district"),
                "state": state["dgms_document"].get("mine_details", {}).get("state"),
                "date": state["dgms_document"].get("accident_date"),
            }
            await self.publish("scan_news_for_incident", incident_details)
        return {}

    async def wait_for_news_scan_node(self, state: IncidentAnalysisState) -> dict:
        print(f"[{self.name}] Waiting for news scan results...")
        await self.news_scan_complete.wait()
        self.news_scan_complete.clear()
        return {"news_scan_results": self.last_news_scan_results}

    async def handle_news_scan_results(self, message):
        print(f"[{self.name}] Received news scan results.")
        self.last_news_scan_results = message["payload"]
        self.news_scan_complete.set()

    async def update_dgms_db_node(self, state: IncidentAnalysisState) -> dict:
        print(f"[{self.name}] Updating DGMS report in DB with verification status...")
        if state["dgms_document"] is None or state["news_scan_results"] is None:
            print("Cannot update DGMS DB: missing document or news scan results.")
            return {}

        coll = self.add_db_tool.coll # Re-use the collection from add_db_tool
        report_id = state["dgms_document"].get("report_id")
        if not report_id:
            print("Cannot update DGMS DB: report_id missing from document.")
            return {}

        articles = state["news_scan_results"].get("articles", [])
        status = "verified" if articles else "unverified"

        update_data = {
            "verification": {
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "articles": [article["url"] for article in articles],
            }
        }
        try:
            await asyncio.to_thread(coll.update_one, {"report_id": report_id}, {"$set": update_data})
            print(f"DGMS report {report_id} updated with verification status: {status}")
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

    @staticmethod
    async def _call_maybe_awaitable(func, *args, timeout=None, **kwargs):
        """
        Call func(*args, **kwargs). If it returns an awaitable, await it.
        If it's a regular function, run it in a thread via asyncio.to_thread.
        Optionally apply timeout (seconds).
        """
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            # sync function raised immediately
            raise

        if asyncio.iscoroutine(result) or inspect.isawaitable(result):
            if timeout:
                return await asyncio.wait_for(result, timeout=timeout)
            return await result
        else:
            # sync result or blocking function: run in thread
            if timeout:
                return await asyncio.wait_for(asyncio.to_thread(lambda: result), timeout=timeout)
            return await asyncio.to_thread(lambda: result)


    async def handle_user_query(self, message):
        query = message["payload"]["query"]
        print(f"[{self.name}] handle_user_query: {query!r}")

        try:
            # 1) get standalone question (likely sync): use helper
            print(f"[{self.name}] Getting standalone question...")
            standalone_question = await self._call_maybe_awaitable(
                get_standalone_question,
                self.contextualize_q_chain,
                self.chat_history,
                query,
                timeout=30,
            )
            print(f"[{self.name}] Standalone question: {standalone_question!r}")

            # 2) retrieve from vector store and mongo in parallel (non-blocking)
            loop = asyncio.get_running_loop()
            retrieve_chroma = loop.run_in_executor(None, retrieve_from_chroma, self.vector_store, standalone_question)
            retrieve_mongo = loop.run_in_executor(None, retrieve_from_mongodb, self.mongo_collection, standalone_question)
            scored_chroma_docs, mongo_contexts = await asyncio.gather(retrieve_chroma, retrieve_mongo)

            print(f"[{self.name}] Retrieved {len(scored_chroma_docs)} chroma docs and {len(mongo_contexts)} mongo contexts.")

            top_chroma_score = 0.0
            chroma_docs = []
            if scored_chroma_docs:
                # scored_chroma_docs is list of (doc, score) pairs per your code earlier
                top_chroma_score = scored_chroma_docs[0][1]
                chroma_docs = [doc for doc, score in scored_chroma_docs]
            chroma_context_str = format_docs(chroma_docs)
            mongo_context_str = "\n\n".join(mongo_contexts)

            combined_context = (
                f"--- PDF Context (Historical) ---\n{chroma_context_str}\n\n"
                f"--- Real-time Data (Live) ---\n{mongo_context_str}"
            )

            # 3) call QA chain safely (it may be async or sync)
            print(f"[{self.name}] Invoking QA chain (with timeout)...")
            # you can tune timeout (e.g., 60s)
            qa_timeout = int(os.environ.get("QA_TIMEOUT_SEC", "60"))
            answer = await self._call_maybe_awaitable(
                self.qa_chain.invoke,
                {
                    "input": query,
                    "chat_history": self.chat_history,
                    "context": combined_context
                },
                timeout=qa_timeout
            )

            # 4) update chat history with lock
            async with self.chat_history_lock:
                # keep a bounded history if needed
                MAX_HISTORY = 50
                self.chat_history.append(HumanMessage(content=query))
                self.chat_history.append(AIMessage(content=answer))
                if len(self.chat_history) > MAX_HISTORY:
                    # drop oldest pair
                    self.chat_history = self.chat_history[-MAX_HISTORY:]

            # 5) publish final answer (ensure publish is awaitable)
            print(f"[{self.name}] Publishing final answer...")
            publish_coro = self.publish("final_answer", {"answer": answer})
            if inspect.isawaitable(publish_coro):
                await publish_coro
            else:
                # publish may be sync, run in thread
                await asyncio.to_thread(lambda: publish_coro)

            print(f"[{self.name}] Final answer published.")

        except asyncio.TimeoutError:
            tb = traceback.format_exc()
            print(f"[{self.name}] QA timed out. {tb}")
            await self.publish("final_answer", {"answer": "The system timed out while generating an answer. Try again later."})
        except Exception as e:
            tb = traceback.format_exc()
            print(f"[{self.name}] ERROR in handle_user_query: {e}\n{tb}")
            try:
                await self.publish("final_answer", {"answer": "I encountered an internal error. Please try again."})
            except Exception:
                # swallow publish failure to avoid crashing
                print(f"[{self.name}] Failed to publish error message.")

    async def _run_periodic_analysis(self):
        while self.running:
            print(f"[{self.name}] Running periodic analysis...")
            analysis_report = await asyncio.to_thread(self.analyze_patterns_tool.use)
            print(f"[{self.name}] Analysis Report: {analysis_report[:200]}...")
            if analysis_report and "Error" not in analysis_report:
                # Save raw analysis report
                analysis_filename = f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                analysis_path = DATA_DIR / analysis_filename
                with open(analysis_path, "w", encoding="utf-8") as f:
                    f.write(analysis_report)
                print(f"[{self.name}] Raw analysis report saved to {analysis_path}")
                await self.publish("analysis_report_saved", {"report_path": str(analysis_path)})

                alerts = await asyncio.to_thread(self.generate_alerts_tool.use, analysis_report)
                if alerts:
                    # Save generated alerts
                    alerts_filename = f"safety_alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    alerts_path = DATA_DIR / alerts_filename
                    with open(alerts_path, "w", encoding="utf-8") as f:
                        json.dump(alerts, f, ensure_ascii=False, indent=2)
                    print(f"[{self.name}] Safety alerts saved to {alerts_path}")
                    await self.publish("safety_alerts_saved", {"alerts_path": str(alerts_path)})

                    for alert in alerts:
                        print(f"[{self.name}] Generated Alert: {alert}")
                        await self.publish("safety_alert", {"alert_message": alert})
            await asyncio.sleep(3600) # Run analysis every hour

    async def _run_periodic_report_generation(self):
        while self.running:
            print(f"[{self.name}] Running periodic audit report generation...")
            report_path = await asyncio.to_thread(self.generate_audit_tool.use)
            print(f"[{self.name}] Audit Report: {report_path}")
            await self.publish("audit_report_generated", {"report_path": report_path})
            await asyncio.sleep(86400) # Generate report every 24 hours

    async def run(self):
        asyncio.create_task(self._run_periodic_analysis())
        asyncio.create_task(self._run_periodic_report_generation())
        while self.running:
            await asyncio.sleep(1) # Keep agent alive
