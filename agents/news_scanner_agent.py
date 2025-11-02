
import asyncio
from utility.agent_framework import Agent
from utility.tools.monitor_news import MonitorNewsTool

class NewsScannerAgent(Agent):
    def __init__(self, name, message_bus):
        super().__init__(name, message_bus)
        self.monitor_news_tool = MonitorNewsTool()
        self.seen_articles = set() # To avoid reprocessing the same articles
        self.subscribe("scan_news_for_incident", self.handle_scan_request)

    async def run(self):
        while self.running:
            print(f"Agent {self.name} is scanning for news...")
            query = "recent coal mining accidents in India"
            articles = self.monitor_news_tool.use(query, desired_count=10)

            for article in articles:
                if article["url"] not in self.seen_articles:
                    print(f"Agent {self.name} found new article: {article["title"]}")
                    await self.publish("new_news_article", article)
                    self.seen_articles.add(article["url"])
            
            await asyncio.sleep(300) # Scan every 5 minutes

    async def handle_scan_request(self, message):
        incident_details = message["payload"]
        mine_name = incident_details.get("mine_name", "")
        district = incident_details.get("district", "")
        state = incident_details.get("state", "")
        date = incident_details.get("date", "")

        query = f'{mine_name} mine accident in {district}, {state} on {date}'
        print(f"[{self.name}] Received scan request with query: {query}")
        articles = self.monitor_news_tool.use(query, desired_count=5)
        await self.publish("news_scan_results", {"articles": articles})
