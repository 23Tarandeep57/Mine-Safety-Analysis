import asyncio
from dotenv import load_dotenv
from utility.agent_framework import MessageBus, Agent
from agents.news_scanner_agent import NewsScannerAgent
from agents.dgms_monitor_agent import DGMSMonitorAgent
from agents.incident_analysis_agent import IncidentAnalysisAgent

from agents.conversational_agent import ConversationalAgent
from utility.local_search import google_web_search
from utility.chatbot_utils import load_api_key, initialize_components, create_manual_chains


load_dotenv()

async def main():
    message_bus = MessageBus()

    # Initialize chatbot components
    api_key = load_api_key()
    llm, vector_store, mongo_collection = initialize_components(api_key, "./chroma_db")
    contextualize_q_chain, qa_chain = create_manual_chains(llm)

    agents = [
        NewsScannerAgent("news_scanner", message_bus),
        DGMSMonitorAgent("dgms_monitor", message_bus),
        IncidentAnalysisAgent("incident_analysis", message_bus, google_web_search, llm, vector_store, mongo_collection, contextualize_q_chain, qa_chain),

        ConversationalAgent("conversational_agent", message_bus),
    ]

    message_bus_task = asyncio.create_task(message_bus.run())

 
    agent_tasks = [asyncio.create_task(agent.start()) for agent in agents]

    print("Mine Safety Multi-Agent System is running.")


    await asyncio.gather(message_bus_task, *agent_tasks)

if __name__ == "__main__":
    asyncio.run(main())