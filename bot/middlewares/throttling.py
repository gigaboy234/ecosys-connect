import time
from collections import defaultdict
from typing import Any, Callable

from vkbottle.dispatch.middlewares.base import BaseMiddleware
from vkbottle.bot import Message


class ThrottlingMiddleware(BaseMiddleware[Message]):
    def __init__(self, rate_limit: float = 1.0) -> None:
        self.rate_limit = rate_limit
        self._last: dict[int, float] = defaultdict(float)

    async def pre(self) -> None:
        user_id = self.event.from_id
        now = time.monotonic()
        if now - self._last[user_id] < self.rate_limit:
            await self.event.answer("⏳ Не так быстро! Подожди секунду.")
            self.stop()
            return
        self._last[user_id] = now
