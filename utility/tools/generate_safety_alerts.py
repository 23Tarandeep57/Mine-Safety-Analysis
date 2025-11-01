import json
import re
from typing import List
from langchain_core.prompts import PromptTemplate
from utility.llm import get_llm

class GenerateSafetyAlertsTool:
    def __init__(self):
        self.name = "generate_safety_alerts"
        self.description = "Generates actionable safety alerts based on an incident pattern analysis report."
        self.llm = get_llm()

    def use(self, analysis_report: str) -> List[str]:
        print("Generating safety alerts...")
        prompt = self._get_alert_generation_prompt(analysis_report)
        try:
            resp = self.llm.invoke(prompt)
            content = resp.content if hasattr(resp, "content") else str(resp)
            
            # Find the start and end of the JSON array
            start_index = content.find('[')
            end_index = content.rfind(']')
            
            if start_index != -1 and end_index != -1:
                json_str = content[start_index : end_index + 1]
                alerts = json.loads(json_str)
                print(f"Generated {len(alerts)} safety alerts.")
                return alerts
            else:
                print("Error: No JSON array found in LLM response.")
                return ["Error: No JSON array found in LLM response."]

        except Exception as e:
            print(f"Error generating alerts with LLM: {e}")
            return [f"Error generating alerts: {e}"]

    def _get_alert_generation_prompt(self, analysis_report: str) -> str:
        return PromptTemplate(
            input_variables=["analysis_report"],
            template=(
                "You are a mine safety expert. Given the following incident pattern analysis report, "
                "identify critical safety issues and formulate concise, actionable safety alerts.\n"
                "Each alert should be a single sentence, focusing on a specific hazard, location, or type of incident. "
                "Return a JSON array of strings, where each string is an alert.\n\n"
                "Analysis Report:\n{analysis_report}\n\n"
                "Example Output: [\"Increase in transportation machinery accidents in Jharkhand mines in Q3 2022.\", \"High incidence of roof falls in underground coal mines in West Bengal.\"]\n\n"
                "Generated Alerts (JSON array):"
            )
        ).format(analysis_report=analysis_report)