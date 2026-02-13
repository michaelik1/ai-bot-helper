from asyncio import run as asyncio_run
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv # remove on docker
from os import getenv
from handlers.echo import handler_echo

async def main():
    bot_key = getenv("TGBOT_KEY")
    bot = Bot(token=bot_key)
    dp = Dispatcher()
    dp.include_router(handler_echo)
    await dp.start_polling(bot)

if __name__ == '__main__':
    load_dotenv() # remove on docker
    asyncio_run(main())
