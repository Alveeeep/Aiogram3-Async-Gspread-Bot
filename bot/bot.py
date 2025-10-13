import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.types import BotCommand, BotCommandScopeDefault, WebAppInfo
from bot.handlers import group_checker
from shared.config import config
from loguru import logger

logger.add(
    "logs/bot.log",
    rotation="10 MB",
    retention="30 days",
    compression="zip",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
)
ALLOWED_UPDATES = ['message, edited_message']
WEBAPP_URL = "https://izomorf.ru"


# Запуск бота
async def main():
    logger.info("Starting bot...")
    bot = Bot(token=config.TOKEN.get_secret_value())
    dp = Dispatcher()
    dp.include_router(group_checker.router)

    @dp.message(Command('start'))
    async def test(message: types.Message):
        await message.answer("Ready")

    commands = [
        BotCommand(command="start", description="🏠 Главное меню"),
    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())

    await bot.set_chat_menu_button(
        menu_button=types.MenuButtonWebApp(
            text="📝 Открыть форму",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    )

    # Запускаем бота и пропускаем все накопленные входящие
    # Да, этот метод можно вызвать даже если у вас поллинг
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot started successfully")
    await dp.start_polling(bot, allowed_updates=ALLOWED_UPDATES)


if __name__ == "__main__":
    asyncio.run(main())
