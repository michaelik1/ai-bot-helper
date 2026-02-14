from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from src.bot.context.states import ModelChoice
from src.bot.keyboards.user import keyboard_default, build_keyboard_models
from src.bot.utils.models_list import models_dict
from src.bot.services.user_manager import UserManager

handler_models = Router()

@handler_models.message(F.text == "🤖Модели")
async def models(message: Message, state: FSMContext):
    user = await UserManager.get_user(message.from_user.id)
    kbd = build_keyboard_models(user.last_model)
    await message.answer("Выберите модель", reply_markup=kbd)
    await state.set_state(ModelChoice.model)

@handler_models.message(ModelChoice.model)
async def model_choice(message: Message, state: FSMContext):
    text = message.text.replace("🔶", "")
    if text in models_dict:
        await state.update_data(model=text)
        await message.answer(f"Установлена модель по умолчанию: {text}", reply_markup=keyboard_default)
        await state.clear()
        user = await UserManager.get_user(message.from_user.id)
        if user.last_model != text:
            user.last_model = text
            user.save()
    else:
        await message.answer("Выберите модель используя отображенные телеграм-кнопки")
