import asyncio

from loguru import logger
from vkbottle import Bot
from vkbottle.dispatch.dispenser import MemoryStateDispenser

from bot.config import settings
from bot.database.db import init_db
from bot.handlers import admin, partner, requests, search, start, startup, student, teacher


async def main() -> None:
    logger.info("Initialising database...")
    await init_db()

    bot = Bot(token=settings.vk_token)
    bot.state_dispenser = MemoryStateDispenser()

    bot.labeler.load(start.labeler)
    bot.labeler.load(student.labeler)
    bot.labeler.load(startup.labeler)
    bot.labeler.load(teacher.labeler)
    bot.labeler.load(partner.labeler)
    bot.labeler.load(search.labeler)
    bot.labeler.load(requests.labeler)
    bot.labeler.load(admin.labeler)

    logger.info("VK Bot started. Long polling...")
    await bot.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
