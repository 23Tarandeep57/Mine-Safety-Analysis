

import asyncio
from utility.agent_framework import Agent
from utility.tools.run_mine_simulation import RunMineSimulationTool

class SimulationAgent(Agent):
    def __init__(self, name, message_bus):
        super().__init__(name, message_bus)
        self.simulation_tool = RunMineSimulationTool()

    async def run(self):
        while self.running:
            print(f"Agent {self.name} is running mine simulation...")
            hazards = await asyncio.to_thread(self.simulation_tool.use, num_readings=5)

            for hazard in hazards:
                print(f"Agent {self.name} detected hazard: {hazard["hazard"]}")
                await self.publish("hazard_alert", hazard)
            
            await asyncio.sleep(60) # Run simulation every minute
