import asyncio
from dotenv import load_dotenv
from utility.agent_framework import MessageBus, Agent
from agents.news_scanner_agent import NewsScannerAgent
from agents.dgms_monitor_agent import DGMSMonitorAgent
from agents.incident_analysis_agent import IncidentAnalysisAgent
from agents.simulation_agent import SimulationAgent
from utility.local_search import google_web_search

# It's a good practice to load environment variables at the start of your application
load_dotenv()

async def main():
    message_bus = MessageBus()

    agents = [
        NewsScannerAgent("news_scanner", message_bus),
        DGMSMonitorAgent("dgms_monitor", message_bus),
        IncidentAnalysisAgent("incident_analysis", message_bus, google_web_search),
        SimulationAgent("simulation", message_bus),
    ]

    # Start the message bus in the background
    message_bus_task = asyncio.create_task(message_bus.run())

    # Start all agents
    agent_tasks = [asyncio.create_task(agent.start()) for agent in agents]

    print("Mine Safety Multi-Agent System is running.")

    # Keep the main loop running indefinitely
    await asyncio.gather(message_bus_task, *agent_tasks)

if __name__ == "__main__":
    asyncio.run(main())