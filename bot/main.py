import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from bot.config import settings
from bot.database.db import AsyncSessionLocal, init_db
from bot.handlers import admin, partner, requests, search, start, startup, student, teacher
from bot.middlewares.db import DbSessionMiddleware
from bot.middlewares.throttling import ThrottlingMiddleware


async def main() -> None:
    logger.info("Initialising database...")
    await init_db()

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    # Middlewares
    dp.update.middleware(DbSessionMiddleware(AsyncSessionLocal))
    dp.message.middleware(ThrottlingMiddleware(rate_limit=1.0))

    # Routers (порядок важен: start первым, потом специфичные)
    dp.include_router(start.router)
    dp.include_router(student.router)
    dp.include_router(startup.router)
    dp.include_router(teacher.router)
    dp.include_router(partner.router)
    dp.include_router(search.router)
    dp.include_router(requests.router)
    dp.include_router(admin.router)

    logger.info("Bot started.")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
