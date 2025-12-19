import json
import re
from typing import Any, Dict, List, Optional
from langchain_core.prompts import PromptTemplate
from utility.llm import get_llm
from utility.tools.base import Tool
from utility.logger import get_logger

logger = get_logger("tools.query_translator")

# MongoDB Schema for the LLM to understand
MONGODB_SCHEMA = """
Collection: dgms_reports
Fields:
- report_id: string (unique identifier)
- accident_date: string (ISO 8601 date, e.g., "2024-07-23")
- summary: string (LLM-generated summary of incident)
- mine_details: {
    name: string,
    owner: string,
    district: string,
    state: string,
    mineral: string
  }
- incident_details: {
    brief_cause: string,
    cause_code: string (e.g., "3.2 - Dumper"),
    fatalities: [{ name, age, sex, occupation }],
    injuries: [{ name, age, sex, occupation }]
  }
- verification: {
    status: string ("verified", "unverified", "unverified_news_report"),
    articles: [string] (URLs)
  }
- source_url: string
"""

QUERY_TRANSLATION_PROMPT = """You are a MongoDB query expert. Convert the user's natural language question into a valid MongoDB query.

{schema}

Rules:
1. Return ONLY a valid JSON object that can be used with collection.find() or collection.aggregate().
2. For simple queries, use find() format: {{"find": {{}}, "sort": {{}}, "limit": 10}}
3. For aggregations, use aggregate() format: {{"aggregate": [{{"$match": {{...}}}}, ...]}}
4. Use regex for partial string matching: {{"$regex": "pattern", "$options": "i"}}
5. For date ranges, use comparison operators: {{"$gte": "2024-01-01", "$lte": "2024-12-31"}}
6. Always include a reasonable limit (default 10).
7. If the query cannot be translated, return {{"error": "reason"}}.

Examples:
User: "accidents in Jharkhand"
Query: {{"find": {{"mine_details.state": {{"$regex": "jharkhand", "$options": "i"}}}}, "sort": {{"accident_date": -1}}, "limit": 10}}

User: "fatalities in coal mines last year"
Query: {{"find": {{"mine_details.mineral": {{"$regex": "coal", "$options": "i"}}, "accident_date": {{"$gte": "2024-01-01", "$lte": "2024-12-31"}}}}, "sort": {{"accident_date": -1}}, "limit": 10}}

User: "top 5 causes of accidents"
Query: {{"aggregate": [{{"$group": {{"_id": "$incident_details.brief_cause", "count": {{"$sum": 1}}}}}}, {{"$sort": {{"count": -1}}}}, {{"$limit": 5}}]}}

User Question: {question}
MongoDB Query (JSON only):"""


class QueryTranslatorTool(Tool):
    """Tool for translating natural language queries into MongoDB queries."""
    
    def __init__(self):
        super().__init__("query_translator")
        self.llm = get_llm()

    async def run(self, question: str) -> Dict[str, Any]:
        self.log_info(f"Translating query: {question}")
        prompt = PromptTemplate(
            input_variables=["schema", "question"],
            template=QUERY_TRANSLATION_PROMPT
        ).format(schema=MONGODB_SCHEMA, question=question)
        
        try:
            resp = await self.llm.ainvoke(prompt)
            content = resp.content if hasattr(resp, "content") else str(resp)
            
            # Extract JSON from the response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                query = json.loads(json_match.group(0))
                self.log_info(f"Translated query: {query}")
                return query
            else:
                self.log_error("No valid JSON found in LLM response")
                return {"error": "Failed to parse query"}
                
        except json.JSONDecodeError as e:
            self.log_error(f"JSON decode error: {e}")
            return {"error": f"Invalid JSON: {e}"}
        except Exception as e:
            self.log_error(f"Translation failed: {e}")
            return {"error": str(e)}

    def run_sync(self, question: str) -> Dict[str, Any]:
        """Synchronous version for use in non-async contexts."""
        self.logger.info(f"Translating query (sync): {question}")
        prompt = PromptTemplate(
            input_variables=["schema", "question"],
            template=QUERY_TRANSLATION_PROMPT
        ).format(schema=MONGODB_SCHEMA, question=question)
        
        try:
            resp = self.llm.invoke(prompt)
            content = resp.content if hasattr(resp, "content") else str(resp)
            
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                query = json.loads(json_match.group(0))
                self.logger.info(f"Translated query: {query}")
                return query
            else:
                return {"error": "Failed to parse query"}
                
        except Exception as e:
            self.logger.error(f"Translation failed: {e}")
            return {"error": str(e)}
