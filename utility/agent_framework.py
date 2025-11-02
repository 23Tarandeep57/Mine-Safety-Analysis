
import asyncio
from collections import defaultdict

class MessageBus:
    def __init__(self):
        self.subscriptions = defaultdict(list)
        self.queue = asyncio.Queue()

    async def publish(self, message):
        await self.queue.put(message)

    def subscribe(self, message_type, callback):
        self.subscriptions[message_type].append(callback)

    async def run(self):
        while True:
            message = await self.queue.get()
            message_type = message.get("type")
            if message_type in self.subscriptions:
                for callback in self.subscriptions[message_type]:
                    await callback(message)
            self.queue.task_done()

class Agent:
    def __init__(self, name, message_bus):
        self.name = name
        self.message_bus = message_bus
        self.running = False
        self._task = None

    async def start(self):
        self.running = True
        print(f"Agent {self.name} started.")
        self._task = asyncio.create_task(self.run())

    async def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()
        print(f"Agent {self.name} stopped.")

    async def run(self):
        raise NotImplementedError("Each agent must implement its own run method.")

    async def publish(self, message_type, payload):
        message = {
            "from_agent": self.name,
            "type": message_type,
            "payload": payload,
        }
        await self.message_bus.publish(message)

    def subscribe(self, message_type, callback):
        self.message_bus.subscribe(message_type, callback)
