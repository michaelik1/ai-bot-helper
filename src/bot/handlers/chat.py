from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from src.bot.services.user_manager import UserManager
from src.bot.keyboards.user import keyboard_chat, keyboard_default
from src.bot.context.states import Chat
from src.bot.services.api_manager import ApiManager
from src.bot.utils.models_list import models_dict

handler_chat = Router()

async def build_initial_chat_message(user_id: int) -> str:
    user = await UserManager.get_user(user_id)
    text = f"""
<b>💬 Вы начали новый чат</b>

<b>🤖 Модель:</b> <code>{user.last_model}</code>  
<b>📦 Ваш план:</b> <code>{"Premium" if user.is_premium else "Free"}</code>  
<b>⏱ Частота запросов:</b> <code>{"unlimited" if user.is_premium else "1.6s/шт"}</code>

Чтобы писать сообщения — используйте клавиатуру телефона.

Чтобы закончить чат — откройте клавиатуру Telegram и нажмите <b>«Закончить чат»</b>.
    """
    return text

@handler_chat.message(F.text == "💬Новый чат")
async def chat_start(message: Message, state: FSMContext):
    initial_msg = await build_initial_chat_message(message.from_user.id)
    await message.answer(initial_msg, message.from_user.id, parse_mode="HTML",reply_markup=keyboard_chat)
    await state.set_state(Chat.waiting_for_exit)

@handler_chat.message(F.text == "❌Завершить чат")
async def chat_exit(message: Message, state: FSMContext):
    text = "☑️Вы завершили чат"
    await message.answer(text, message.from_user.id, reply_markup=keyboard_default)
    await state.clear()

@handler_chat.message(Chat.waiting_for_exit)
async def chat_continuous_dialog(message):
    user = await UserManager.get_user(message.from_user.id)
    model_short_id = models_dict[user.last_model]
    model_answer = await ApiManager.send_request(model_short_id, message.text)
    await message.answer(model_answer, reply_markup=keyboard_chat)