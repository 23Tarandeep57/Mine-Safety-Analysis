

import asyncio
from utility.agent_framework import Agent
from utility.tools.monitor_website import MonitorWebsiteTool

class DGMSMonitorAgent(Agent):
    def __init__(self, name, message_bus):
        super().__init__(name, message_bus)
        self.monitor_website_tool = MonitorWebsiteTool()

    async def run(self):
        while self.running:
            print(f"Agent {self.name} is monitoring DGMS website...")
            new_reports = await asyncio.to_thread(self.monitor_website_tool.use)

            for report in new_reports:
                print(f"Agent {self.name} found new DGMS report: {report['report_id']}")
                await self.publish("new_dgms_report", report)
            
            await asyncio.sleep(300) # Scan every 5 minutes
