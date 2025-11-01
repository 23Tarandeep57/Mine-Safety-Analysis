
from web_news import get_valid_articles

class MonitorNewsTool:
    def __init__(self):
        self.name = "monitor_news"
        self.description = "Monitors news sources for mining accidents based on a query."

    def use(self, query: str, desired_count: int = 5):
        print(f"Using monitor_news tool with query: {query}")
        articles = get_valid_articles(query, desired_count)
        return articles
