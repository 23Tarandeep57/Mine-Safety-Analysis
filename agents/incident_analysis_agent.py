import asyncio
import json
import redis
import traceback
from typing import Literal, TypedDict, List, Dict, Any, Optional
from datetime import datetime, timezone

from utility.agent_framework import Agent
from utility.config import REDIS_URL, ANALYSIS_INTERVAL_SECONDS, REPORT_GENERATION_INTERVAL_SECONDS, DATA_DIR
from utility.chatbot_utils import get_standalone_question, retrieve_from_chroma, retrieve_from_mongodb, format_docs
from utility.langgraph_orchestrator import LangGraphOrchestrator
from utility.logger import get_logger
from langchain_core.messages import HumanMessage, AIMessage

logger = get_logger("agents.incident_analysis")
EOS_TOKEN = "<EOS>"

class IncidentAnalysisAgent(Agent):
    def __init__(self, name, message_bus, google_web_search_func, llm, vector_store, mongo_collection, contextualize_q_chain, qa_chain):
        super().__init__(name, message_bus)
        self.orchestrator = LangGraphOrchestrator()
        
        self.subscribe("new_news_article", self.handle_news_article)
        self.subscribe("new_dgms_report", self.handle_dgms_report)
        self.subscribe("user_query", self.handle_user_query)
        
        # Chatbot components
        self.llm = llm
        self.vector_store = vector_store
        self.mongo_collection = mongo_collection
        self.contextualize_q_chain = contextualize_q_chain
        self.qa_chain = qa_chain
        self.chat_history = []
        self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)

    async def handle_news_article(self, message):
        article = message["payload"]
        logger.info(f"Received news article: {article.get('title')}")
        try:
            await self.orchestrator.run_pipeline(
                initial_data=article,
                source="news",
                source_url=article.get("link", ""),
                raw_title=article.get("title", "")
            )
        except Exception as e:
            logger.error(f"Error processing news article in LangGraph: {e}")

    async def handle_dgms_report(self, message):
        report = message["payload"]
        logger.info(f"Received DGMS report: {report.get('title')}")
        try:
            await self.orchestrator.run_pipeline(
                initial_data=report,
                source="dgms",
                source_url=report.get("link", ""),
                raw_title=report.get("title", "")
            )
        except Exception as e:
            logger.error(f"Error processing DGMS report in LangGraph: {e}")

    async def handle_user_query(self, message):
        query = message["payload"]["query"]
        request_id = message["payload"].get("request_id")
        logger.info(f"handle_user_query: {query!r} (request_id: {request_id})")

        try:
            standalone_question = await get_standalone_question(self.contextualize_q_chain, self.chat_history, query)
            
            loop = asyncio.get_running_loop()
            retrieve_chroma = loop.run_in_executor(None, retrieve_from_chroma, self.vector_store, standalone_question)
            retrieve_mongo = loop.run_in_executor(None, retrieve_from_mongodb, self.mongo_collection, standalone_question)
            
            scored_chroma_docs, mongo_contexts = await asyncio.gather(retrieve_chroma, retrieve_mongo)

            chroma_docs = [doc for doc, _ in scored_chroma_docs] if scored_chroma_docs else []
            chroma_context_str = format_docs(chroma_docs)
            mongo_context_str = "\n\n".join(mongo_contexts)

            combined_context = (
                f"--- PDF Context (Historical) ---\n{chroma_context_str}\n\n"
                f"--- Real-time Data (Live) ---\n{mongo_context_str}"
            )
            
            full_answer = await asyncio.to_thread(
                self.stream_response_to_redis,
                self.qa_chain,
                self.chat_history,
                query,
                combined_context,
                request_id
            )

            self.chat_history.append(HumanMessage(content=query))
            self.chat_history.append(AIMessage(content=full_answer))

        except Exception as e:
            logger.error(f"ERROR in handle_user_query: {e}")
            if request_id:
                channel = f"chat:response:{request_id}"
                self.redis_client.publish(channel, f"I encountered an error: {e}{EOS_TOKEN}")

    def stream_response_to_redis(self, qa_chain, chat_history, query, context, request_id):
        channel = f"chat:response:{request_id}"
        full_answer = ""
        try:
            for chunk in qa_chain.stream({
                "input": query,
                "chat_history": chat_history,
                "context": context
            }):
                if isinstance(chunk, str):
                    text = chunk
                elif hasattr(chunk, 'content'):
                    text = chunk.content
                elif isinstance(chunk, dict):
                    text = chunk.get('answer', chunk.get('text', chunk.get('output', '')))
                else:
                    text = str(chunk)
                
                if text:
                    self.redis_client.publish(channel, text)
                    full_answer += text
            
            self.redis_client.publish(channel, EOS_TOKEN)
            
        except Exception as e:
            logger.error(f"ERROR in stream_response_to_redis: {e}")
            self.redis_client.publish(channel, f"I encountered an error while streaming.{EOS_TOKEN}")
        
        return full_answer

    async def run(self):
        # The orchestrator handles periodic analysis now if we want, 
        # or we can keep it here but calling the orchestrator nodes.
        # For now, let's just keep the agent alive.
        while self.running:
            await asyncio.sleep(1)