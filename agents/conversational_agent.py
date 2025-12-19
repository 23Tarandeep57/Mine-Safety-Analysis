import asyncio
import json
import redis
from utility.agent_framework import Agent
from utility.config import REDIS_URL
from utility.logger import get_logger

logger = get_logger("agents.conversational")

CHAT_QUEUE = "chat:queue"
NOTIFICATIONS_CHANNEL = "chat:notifications"

class ConversationalAgent(Agent):
    def __init__(self, name, message_bus):
        super().__init__(name, message_bus)
        self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        
        # Subscribe to pipeline events to notify users
        self.subscribe("incident_stored", self.handle_new_incident)
        self.subscribe("safety_alert", self.handle_safety_alert)
        self.subscribe("analysis_complete", self.handle_analysis_complete)
        self.subscribe("pipeline_complete", self.handle_pipeline_complete)
        self.subscribe("news_verification_results", self.handle_verification_results)

    async def run(self):
        logger.info(f"Starting up and listening on Redis queue: {CHAT_QUEUE}")

        while self.running:
            try:
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: self.redis_client.brpop(CHAT_QUEUE, timeout=1)
                )
                
                if result:
                    _, message_json = result
                    message = json.loads(message_json)
                    request_id = message.get("request_id")
                    query = message.get("query")
                    chat_history = message.get("chat_history", [])
                    
                    logger.info(f"Received query: {query[:50]}... (request_id: {request_id})")
                    
                    # Forward to IncidentAnalysisAgent for RAG processing
                    await self.publish("user_query", {
                        "query": query,
                        "request_id": request_id,
                        "chat_history": chat_history
                    })
                    
            except redis.RedisError as e:
                logger.error(f"Redis error: {e}")
                await asyncio.sleep(1)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in queue: {e}")
            except Exception as e:
                logger.error(f"Error processing queue: {e}")
                await asyncio.sleep(0.1)

    def _push_notification(self, notification_type: str, data: dict):
        """Push a notification to the frontend via Redis pub/sub."""
        notification = {
            "type": notification_type,
            "data": data
        }
        try:
            self.redis_client.publish(NOTIFICATIONS_CHANNEL, json.dumps(notification))
            logger.info(f"Pushed notification: {notification_type}")
        except Exception as e:
            logger.error(f"Failed to push notification: {e}")

    async def handle_new_incident(self, message):
        """Notify frontend when a new incident is stored."""
        payload = message["payload"]
        self._push_notification("new_incident", {
            "mine_name": payload.get("mine_name"),
            "source": payload.get("source"),
            "id": payload.get("id")
        })

    async def handle_safety_alert(self, message):
        """Notify frontend of safety alerts."""
        payload = message["payload"]
        self._push_notification("safety_alert", {
            "alert": payload.get("alert"),
            "severity": "high"
        })

    async def handle_analysis_complete(self, message):
        """Notify frontend when analysis is complete."""
        payload = message["payload"]
        self._push_notification("analysis_complete", {
            "report_length": payload.get("report_length")
        })

    async def handle_pipeline_complete(self, message):
        """Notify frontend of pipeline completion."""
        payload = message["payload"]
        self._push_notification("pipeline_complete", {
            "title": payload.get("title"),
            "source": payload.get("source"),
            "alerts_count": payload.get("alerts_count")
        })

    async def handle_verification_results(self, message):
        """Notify frontend of DGMS report verification status."""
        payload = message["payload"]
        self._push_notification("verification_result", {
            "report_id": payload.get("report_id"),
            "verified": payload.get("verified"),
            "articles_count": len(payload.get("articles", []))
        })
