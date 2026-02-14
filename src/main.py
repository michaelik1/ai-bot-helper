from asyncio import run as asyncio_run
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv # remove on docker
from os import getenv
from src.bot.handlers.startup import handler_startup
from src.bot.handlers.models import handler_models
from src.bot.handlers.profile import handler_profile
from src.bot.handlers.rules_and_help import handler_rules
from src.bot.services.user_manager import UserManager

async def main():
    bot_key = getenv("TGBOT_KEY")
    bot = Bot(token=bot_key)
    dp = Dispatcher()
    dp.include_routers(handler_startup, handler_models, handler_profile, handler_rules)
    UserManager.setup()
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        load_dotenv()  # remove on docker
        asyncio_run(main())
    except KeyboardInterrupt:
        print("Keyboard interrupt")
