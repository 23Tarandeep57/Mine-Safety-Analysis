import asyncio
from utility.agent_framework import Agent

class ConversationalAgent(Agent):
    def __init__(self, name, message_bus):
        super().__init__(name, message_bus)
        self.subscribe("final_answer", self.handle_final_answer)

    async def run(self):
        while self.running:
            try:
                with open("user_query.txt", "r+") as f:
                    query = f.read().strip()
                    if query:
                        print(f"[{self.name}] Received query: {query}")
                        await self.publish("user_query", {"query": query})
                        f.truncate(0)
            except FileNotFoundError:
                pass
            await asyncio.sleep(1)

    async def handle_final_answer(self, message):
        answer = message["payload"]["answer"]
        print(f"[{self.name}] Received final answer: {answer}")
        with open("bot_response.txt", "w") as f:
            f.write(answer)
