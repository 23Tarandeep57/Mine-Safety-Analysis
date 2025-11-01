
import json
from langchain_core.prompts import PromptTemplate
from utility.llm import get_llm

class ExtractIncidentFromNewsTool:
    def __init__(self):
        self.name = "extract_incident_from_news"
        self.description = "Extracts structured incident information from a news article using an LLM."
        self.llm = get_llm()

    def use(self, article: dict) -> dict:
        print(f"Extracting incident from news article: {article.get("title", "N/A")}")
        prompt = self._get_extraction_prompt(article)
        try:
            resp = self.llm.invoke(prompt)
            content = resp.content if hasattr(resp, "content") else str(resp)
            json_str = content.strip().replace("```json", "").replace("```", "")
            extracted_data = json.loads(json_str)
            return extracted_data
        except Exception as e:
            print(f"Error extracting incident with LLM: {e}")
            return {"error": str(e)}

    def _get_extraction_prompt(self, article: dict) -> str:
        # Note: The curly braces for the JSON schema are escaped by doubling them (e.g., {{ and }})
        template = """You are an expert at extracting structured information about mining incidents from news articles.
Extract the following details from the provided news article summary and title. Return ONLY a valid JSON object. The `incident_date` MUST be in YYYY-MM-DD format. If the exact date is not mentioned, return null for the `incident_date` field.

Schema: {{
  "incident_date": "YYYY-MM-DD",
  "mine_name": "string",
  "district": "string",
  "state": "string",
  "fatalities": "integer",
  "injuries": "integer",
  "brief_cause": "string"
}}

--- Example ---
News Article Title: Mine Wall Collapse in Dhanbad Kills One, Injures Two | Outlook India
News Article Summary: A wall of an open-cast coal mine in the Putki mining area collapsed on Sunday, killing one person and injuring two others.
Extracted JSON: {{"incident_date": null, "mine_name": "Putki mining area", "district": "Dhanbad", "state": "Jharkhand", "fatalities": 1, "injuries": 2, "brief_cause": "Wall of an open-cast coal mine collapsed."}}
--- End Example ---

News Article Title: {article_title}
News Article Summary: {article_summary}
Extracted JSON:"""
        return PromptTemplate(
            input_variables=["article_title", "article_summary"],
            template=template
        ).format(article_title=article.get("title", ""), article_summary=article.get("summary", ""))
