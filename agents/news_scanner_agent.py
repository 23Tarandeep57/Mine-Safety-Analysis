
import asyncio
from utility.agent_framework import Agent
from utility.tools.monitor_news import MonitorNewsTool
from utility.logger import get_logger

logger = get_logger("agents.news_scanner")

class NewsScannerAgent(Agent):
    def __init__(self, name, message_bus):
        super().__init__(name, message_bus)
        self.monitor_news_tool = MonitorNewsTool()
        self.seen_articles = set()
        
        # Subscribe to verification requests from LangGraph pipeline
        self.subscribe("request_news_verification", self.handle_verification_request)
        self.subscribe("scan_news_for_incident", self.handle_scan_request)

    async def run(self):
        while self.running:
            logger.info("Scanning for news...")
            query = "recent coal mining accidents in India"
            articles = await asyncio.to_thread(self.monitor_news_tool.use, query, desired_count=1)

            for article in articles:
                if article["url"] not in self.seen_articles:
                    logger.info(f"Found new article: {article['title']}")
                    await self.publish("new_news_article", article)
                    self.seen_articles.add(article["url"])
            
            await asyncio.sleep(900)  # Scan every 15 minutes

    async def handle_verification_request(self, message):
        """Handle news verification requests from DGMS pipeline."""
        payload = message["payload"]
        mine_name = payload.get("mine_name", "")
        district = payload.get("district", "")
        state = payload.get("state", "")
        date = payload.get("date", "")
        report_id = payload.get("report_id", "")

        query = f'{mine_name} mine accident in {district}, {state} {date}'
        logger.info(f"Verification request for report {report_id}: {query}")
        
        articles = await asyncio.to_thread(self.monitor_news_tool.use, query, desired_count=3)
        
        # Publish verification results
        await self.publish("news_verification_results", {
            "report_id": report_id,
            "query": query,
            "articles": articles,
            "verified": len(articles) > 0
        })

    async def handle_scan_request(self, message):
        """Handle ad-hoc scan requests from other agents."""
        incident_details = message["payload"]
        mine_name = incident_details.get("mine_name", "")
        district = incident_details.get("district", "")
        state = incident_details.get("state", "")
        date = incident_details.get("date", "")

        query = f'{mine_name} mine accident in {district}, {state} on {date}'
        logger.info(f"Scan request received: {query}")
        
        articles = await asyncio.to_thread(self.monitor_news_tool.use, query, desired_count=3)
        await self.publish("news_scan_results", {"articles": articles, "query": query})