from aiogram import Router
from aiogram.types import Message

handler_echo = Router()

@handler_echo.message()
async def echo(message: Message):
    await message.send_copy(chat_id=message.from_user.id)
