
import asyncio
import json
from dotenv import load_dotenv
from utility.tools.collect_reports import CollectReportsTool
from utility.tools.enrich_locations import EnrichLocationsTool
from utility.tools.analyze_reports import AnalyzeReportsTool
from utility.tools.monitor_website import MonitorWebsiteTool
from utility.tools.verify_report_with_news import VerifyReportWithNewsTool
from utility.task import Task
from default_api import google_web_search
from utility.llm import get_llm

# It's a good practice to load environment variables at the start of your application
load_dotenv()

class MineSafetyAgent:
    def __init__(self):
        self.tools = self._load_tools()
        self.tasks = []

    def _load_tools(self):
        # This is where we will load our tools from the utility/tools directory
        print("Loading tools...")
        collect_reports_tool = CollectReportsTool()
        enrich_locations_tool = EnrichLocationsTool()
        analyze_reports_tool = AnalyzeReportsTool()
        monitor_website_tool = MonitorWebsiteTool(self)
        verify_report_with_news_tool = VerifyReportWithNewsTool(self)
        return {
            collect_reports_tool.name: collect_reports_tool,
            enrich_locations_tool.name: enrich_locations_tool,
            analyze_reports_tool.name: analyze_reports_tool,
            monitor_website_tool.name: monitor_website_tool,
            verify_report_with_news_tool.name: verify_report_with_news_tool,
        }

    def add_task(self, task):
        self.tasks.append(task)

    def get_plan_llm(self):
        print("Getting plan from LLM...")
        llm = get_llm()
        prompt = self.get_llm_prompt()
        try:
            resp = llm.invoke(prompt)
            content = resp.content if hasattr(resp, "content") else str(resp)
            json_str = content.strip().replace("```json", "").replace("```", "")
            plan = json.loads(json_str)
            return [Task(task["name"], task.get("params", {})) for task in plan]
        except Exception as e:
            print(f"Error getting plan from LLM: {e}")
            return None

    def get_llm_prompt(self):
        tool_descriptions = "\n".join([f"- {name}: {tool.description}" for name, tool in self.tools.items()])
        return f"""You are a mine safety agent. Your goal is to collect, analyze, and verify mine safety reports.

Available tools:
{tool_descriptions}

Your current task queue is empty. What is your plan? Return a JSON array of tasks.
Example: [ {{"name": "monitor_website", "params": {{}}}}, {{"name": "analyze_reports", "params": {{}}}} ]
"""

    async def run(self):
        print("Mine Safety Agent is running.")
        while True:
            if self.tasks:
                task = self.tasks.pop(0)
                print(f"Executing task: {task.name}")
                if task.name in self.tools:
                    self.tools[task.name].use(**task.params)
                else:
                    print(f"Unknown task: {task.name}")
            else:
                print("No tasks to execute. Getting new plan from LLM.")
                plan = self.get_plan_llm()
                if plan:
                    self.tasks.extend(plan)
                else:
                    print("Could not get plan from LLM. Sleeping for a minute.")
                    await asyncio.sleep(60)

    def google_web_search(self, query):
        return google_web_search(query=query)


def main():
    agent = MineSafetyAgent()
    asyncio.run(agent.run())

if __name__ == "__main__":
    main()
