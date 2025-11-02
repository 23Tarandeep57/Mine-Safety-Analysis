from typing import List
from langchain_core.prompts import PromptTemplate
from utility.llm import get_llm

class GenerateRecommendationsTool:
    def __init__(self):
        self.name = "generate_recommendations"
        self.description = "Generates actionable safety recommendations based on an incident pattern analysis report."
        self.llm = get_llm()

    def use(self, analysis_report: str) -> List[str]:
        print("Generating safety recommendations...")
        prompt = self._get_recommendation_generation_prompt(analysis_report)
        try:
            resp = self.llm.invoke(prompt)
            content = resp.content if hasattr(resp, "content") else str(resp)
            # Split the response into a list of recommendations
            recommendations = [rec.strip() for rec in content.split("\n") if rec.strip()]
            print(f"Generated {len(recommendations)} safety recommendations.")
            return recommendations
        except Exception as e:
            print(f"Error generating recommendations with LLM: {e}")
            return [f"Error generating recommendations: {e}"]

    def _get_recommendation_generation_prompt(self, analysis_report: str) -> str:
        return PromptTemplate(
            input_variables=["analysis_report"],
            template=(
                "You are a mine safety expert with decades of experience. Given the following incident pattern analysis report, "
                "your task is to provide a set of clear, concise, and actionable safety recommendations. Each recommendation should be a single sentence and start with an action verb (e.g., 'Implement', 'Conduct', 'Ensure')."
                "Focus on practical steps that can be taken to mitigate the identified risks. Do not number the recommendations."
                "\n\nAnalysis Report:\n{analysis_report}\n\n"
                "Generated Recommendations (one per line):"
            )
        ).format(analysis_report=analysis_report)
