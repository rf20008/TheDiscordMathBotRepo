import disnake
import time
import asyncio
import heapq
import fractions
class MessageThing:
    priority: int
    stuff: dict
    to: disnake.abc.Messageable
    time_created: float
    def __init__(self, to: disnake.abc.Messageable, stuff: dict, priority: int = 3000):
        self.to = to
        self.stuff = stuff
        self.priority = priority
        self.time_created = time.time()
    @property
    def age(self):
        return time.time()-self.time_created
    def __eq__(self, other):
        return (
            self.to == other.to
            and self.stuff == other.stuff
            and self.priority == other.priority
        )

    def __le__(self, other):
        return self<other or self==other

    def __lt__(self, other):
        if self.priority !=  other.priority:
            return self.priority < other.priority
        if self.age != other.age:
            return self.age > other.age
        return False

    async def send(self):
        await self.to.send(**self.stuff)

    def decrement_priority(self):
        self.priority -= 1


class MessageQueue:
    heap: list[MessageThing]
    lock: asyncio.Lock
    __slots__ = ('heap', 'lock')
    def __init__(self):
        self.heap = []
        self.lock = asyncio.Lock()
    def is_empty(self):
        return len(self.heap) == 0
    async def decrement_priorities_periodically(self, interval=60):
        while True:
            await asyncio.sleep(interval)
            await self.decrement_priorities()
    async def decrement_priorities(self):
        async with self.lock:
            for item in self.heap:
                item.decrement_priority()
            heapq.heapify(self.heap)
    async def send_periodically(self, interval=1):
        while True:
            await asyncio.sleep(interval)
            if self.is_empty():
                continue
            await self.send_top()
    async def send_top(self):
        if self.is_empty():
            raise IndexError("Cannot send message from an empty MessageQueue")
        top = None
        async with self.lock:
            top = heapq.heappop(self.heap)
        await top.send()

    async def send_every_so_often(self, APIRQPS = fractions.Fraction(1, 2)):
        await self.send_periodically(1/APIRQPS)

    async def add_message(self, message: MessageThing):
        async with self.lock:
            heapq.heappush(self.heap, message)
