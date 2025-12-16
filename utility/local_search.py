"""
Local Search Utility using Tavily API

Provides web search functionality as a replacement for Google Web Search.
Requires TAVILY_API_KEY environment variable.
"""

import os

# Tavily client initialization - only if API key is available
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
tavily_client = None

if TAVILY_API_KEY:
    try:
        from tavily import TavilyClient
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
    except ImportError:
        print("Warning: tavily package not installed. Web searches will be disabled.")
else:
    print("Warning: TAVILY_API_KEY not set. Tavily searches will be disabled.")


def google_web_search(query: str) -> dict:
    """
    Performs a web search using the Tavily API.
    This function is a local replacement for the `default_api.google_web_search` tool.
    
    Returns empty results if Tavily is not configured.
    """
    if tavily_client is None:
        print(f"--- Tavily not configured, skipping search: {query} ---")
        return {"results": []}
    
    print(f"--- Performing local search with Tavily: {query} ---")
    try:
        response = tavily_client.search(
            query=query,
            search_depth="basic",
            max_results=10,
        )
        return {"results": response.get("results", [])}
    except Exception as e:
        print(f"Error performing Tavily search: {e}")
        return {"results": []}
