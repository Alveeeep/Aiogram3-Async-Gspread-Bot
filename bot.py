import asyncio
from aiogram import Bot, Dispatcher
from handlers import group_checker
from config import config
import logging

logger = logging.getLogger(__name__)
ALLOWED_UPDATES = ['message, edited_message']


# Запуск бота
async def main():
    logger.info("Starting bot...")
    bot = Bot(token=config.TOKEN.get_secret_value())
    dp = Dispatcher()
    dp.include_router(group_checker.router)

    # Запускаем бота и пропускаем все накопленные входящие
    # Да, этот метод можно вызвать даже если у вас поллинг
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=ALLOWED_UPDATES)


if __name__ == "__main__":
    asyncio.run(main())
