
import asyncio
from utility.agent_framework import Agent
from utility.tools.monitor_website import MonitorWebsiteTool
from utility.logger import get_logger

logger = get_logger("agents.dgms_monitor")

class DGMSMonitorAgent(Agent):
    def __init__(self, name, message_bus):
        super().__init__(name, message_bus)
        self.monitor_website_tool = MonitorWebsiteTool()
        
        # Subscribe to pipeline events for feedback
        self.subscribe("incident_stored", self.handle_incident_stored)
        self.subscribe("news_verification_results", self.handle_verification_results)

    async def run(self):
        while self.running:
            logger.info("Monitoring DGMS website...")
            new_reports = await asyncio.to_thread(self.monitor_website_tool.use)

            for report in new_reports:
                logger.info(f"Found new DGMS report: {report['report_id']}")
                await self.publish("new_dgms_report", report)
            
            await asyncio.sleep(60)  # Scan every minute

    async def handle_incident_stored(self, message):
        """React when an incident from this agent is stored."""
        payload = message["payload"]
        if payload.get("source") == "dgms":
            logger.info(f"DGMS report stored: {payload.get('id')}")

    async def handle_verification_results(self, message):
        """React to news verification results for DGMS reports."""
        payload = message["payload"]
        report_id = payload.get("report_id")
        verified = payload.get("verified", False)
        articles = payload.get("articles", [])
        
        if verified:
            logger.info(f"Report {report_id} VERIFIED with {len(articles)} news articles")
        else:
            logger.warning(f"Report {report_id} could not be verified with news sources")
