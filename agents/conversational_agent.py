import asyncio
from utility.agent_framework import Agent
from utility.config import DATA_DIR

USER_QUERY_FILE = DATA_DIR / "user_query.txt"
BOT_RESPONSE_FILE = DATA_DIR / "bot_response.txt"

class ConversationalAgent(Agent):
    def __init__(self, name, message_bus):
        super().__init__(name, message_bus)
        self.subscribe("final_answer", self.handle_final_answer)

    async def run(self):
        print(f"[{self.name}] Starting up and watching {USER_QUERY_FILE}")
        # Ensure the files exist and are empty on startup
        open(USER_QUERY_FILE, "w").close()
        open(BOT_RESPONSE_FILE, "w").close()

        while self.running:
            try:
                with open(USER_QUERY_FILE, "r+") as f:
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
        with open(BOT_RESPONSE_FILE, "w") as f:
            f.write(answer)
