from aiogram import Router
from aiogram.types import Message

handler_models = Router()

@handler_models.message("🤖Модели")
async def models(message: Message):
    pass