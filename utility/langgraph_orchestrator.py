from typing import Annotated, Any, Dict, List, Optional, TypedDict, Union
from langgraph.graph import StateGraph, END
from utility.logger import get_logger
from utility.tools.extractor import ExtractorTool
from utility.tools.deduplicator import DeduplicatorTool
from utility.tools.enricher import EnricherTool
from utility.tools.storage import StorageTool
from utility.tools.analyzer import AnalyzerTool
from utility.tools.alerter import AlerterTool

logger = get_logger("langgraph.orchestrator")

class IncidentState(TypedDict):
    """The state of an incident as it moves through the pipeline."""
    raw_data: Dict[str, Any]
    source: str  # 'dgms' or 'news'
    source_url: str
    raw_title: str
    extracted_incident: Optional[Dict[str, Any]]
    is_duplicate: bool
    enriched_data: Optional[Dict[str, Any]]
    analysis_results: Optional[str]
    alerts: List[str]
    errors: List[str]

class LangGraphOrchestrator:
    def __init__(self):
        self.extractor = ExtractorTool()
        self.deduplicator = DeduplicatorTool()
        self.enricher = EnricherTool()
        self.storage = StorageTool()
        self.analyzer = AnalyzerTool()
        self.alerter = AlerterTool()
        
        self.builder = StateGraph(IncidentState)
        self._setup_graph()
        self.graph = self.builder.compile()

    def _setup_graph(self):
        # Define Nodes
        self.builder.add_node("extract", self.extract_node)
        self.builder.add_node("deduplicate", self.deduplicate_node)
        self.builder.add_node("enrich", self.enrich_node)
        self.builder.add_node("store", self.store_node)
        self.builder.add_node("analyze", self.analyze_node)
        self.builder.add_node("alert", self.alert_node)

        # Define Edges
        self.builder.set_entry_point("extract")
        self.builder.add_edge("extract", "deduplicate")
        
        self.builder.add_conditional_edges(
            "deduplicate",
            self.should_continue,
            {
                "continue": "enrich",
                "stop": END
            }
        )
        
        self.builder.add_edge("enrich", "store")
        self.builder.add_edge("store", "analyze")
        self.builder.add_edge("analyze", "alert")
        self.builder.add_edge("alert", END)

    async def extract_node(self, state: IncidentState) -> Dict[str, Any]:
        logger.info("Node: extract", extra={"extra": {"source": state.get("source")}})
        extracted = await self.extractor.run(state["raw_data"])
        return {"extracted_incident": extracted}

    async def deduplicate_node(self, state: IncidentState) -> Dict[str, Any]:
        logger.info("Node: deduplicate")
        if not state.get("extracted_incident"):
            return {"is_duplicate": False}
        is_dup = await self.deduplicator.run(state["extracted_incident"])
        return {"is_duplicate": is_dup}

    async def enrich_node(self, state: IncidentState) -> Dict[str, Any]:
        logger.info("Node: enrich")
        if not state.get("extracted_incident"):
            return {"enriched_data": None}
        enriched = await self.enricher.run(state["extracted_incident"])
        return {"enriched_data": enriched}

    async def store_node(self, state: IncidentState) -> Dict[str, Any]:
        logger.info("Node: store")
        if not state.get("enriched_data"):
            return {}
        result = await self.storage.run(
            state["enriched_data"], 
            state["source_url"], 
            state["raw_title"]
        )
        return {"storage_result": result}

    async def analyze_node(self, state: IncidentState) -> Dict[str, Any]:
        logger.info("Node: analyze")
        report = await self.analyzer.run()
        return {"analysis_results": report}

    async def alert_node(self, state: IncidentState) -> Dict[str, Any]:
        logger.info("Node: alert")
        if not state.get("analysis_results"):
            return {"alerts": []}
        alerts = await self.alerter.run(state["analysis_results"])
        return {"alerts": alerts}

    def should_continue(self, state: IncidentState) -> str:
        if state.get("is_duplicate"):
            logger.info("Duplicate detected, stopping pipeline.")
            return "stop"
        return "continue"

    async def run_pipeline(self, initial_data: Dict[str, Any], source: str, source_url: str, raw_title: str):
        initial_state: IncidentState = {
            "raw_data": initial_data,
            "source": source,
            "source_url": source_url,
            "raw_title": raw_title,
            "extracted_incident": None,
            "is_duplicate": False,
            "enriched_data": None,
            "analysis_results": None,
            "alerts": [],
            "errors": []
        }
        try:
            return await self.graph.ainvoke(initial_state)
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise
