from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from src.bot.context.states import ModelChoice
from src.bot.keyboards.user import keyboard_models, keyboard_default
from src.bot.utils.models_list import models_dict

handler_models = Router()

@handler_models.message(F.text == "🤖Модели")
async def models(message: Message, state: FSMContext):
    await message.answer("Выберите модель", reply_markup=keyboard_models)
    await state.set_state(ModelChoice.model)

@handler_models.message(ModelChoice.model)
async def model_choice(message: Message, state: FSMContext):
    if message.text in models_dict:
        await state.update_data(model=message.text)
        await message.answer(f"Установлена модель по умолчанию: {message.text}", reply_markup=keyboard_default)
        await state.clear()
    else:
        await message.answer("Выберите модель используя отображенные телеграм-кнопки")
