import os
from tavily import TavilyClient

# Initialize the Tavily client from your .env file
tavily_client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))

def google_web_search(query: str) -> dict:
    """
    Performs a web search using the Tavily API.
    This function is a local replacement for the `default_api.google_web_search` tool.
    """
    print(f"--- Performing local search with Tavily: {query} ---")
    try:
        response = tavily_client.search(
            query=query,
            search_depth="basic",  # Use "basic" for speed, or "advanced" for more detail
            max_results=10,
        )
        # The Tavily API returns a list of results, so we wrap it in a dictionary
        # to match the expected output of the original `google_web_search` tool.
        return {"results": response.get("results", [])}
    except Exception as e:
        print(f"Error performing Tavily search: {e}")
        return {"results": []}
