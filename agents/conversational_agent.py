import asyncio
import json
import redis
from utility.agent_framework import Agent
from utility.config import REDIS_URL

CHAT_QUEUE = "chat:queue"

class ConversationalAgent(Agent):
    def __init__(self, name, message_bus):
        super().__init__(name, message_bus)
        self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        # We no longer need to handle final_answer - responses go directly via Redis pub/sub

    async def run(self):
        print(f"[{self.name}] Starting up and listening on Redis queue: {CHAT_QUEUE}")

        while self.running:
            try:
                # BRPOP blocks until a message is available (timeout=1 second)
                # Run in executor to not block the async loop
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
                    
                    print(f"[{self.name}] Received query from Redis: {query[:50]}... (request_id: {request_id})")
                    
                    # Publish to internal message bus for IncidentAnalysisAgent
                    await self.publish("user_query", {
                        "query": query,
                        "request_id": request_id,
                        "chat_history": chat_history
                    })
                    
            except redis.RedisError as e:
                print(f"[{self.name}] Redis error: {e}")
                await asyncio.sleep(1)  # Wait before retry
            except json.JSONDecodeError as e:
                print(f"[{self.name}] Invalid JSON in queue: {e}")
            except Exception as e:
                print(f"[{self.name}] Error processing queue: {e}")
                await asyncio.sleep(0.1)
