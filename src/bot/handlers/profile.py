from aiogram import Router, F
from aiogram.types import Message
from src.bot.services.user_manager import UserManager

handler_profile = Router()

async def build_profile_message(user_id: int) -> str:
    user = await UserManager.get_user(user_id)
    text = f"""
<b>👤 Ваш профиль</b>

<b>🆔 ID:</b> <code>{user.id}</code>
<b>💰 Баланс:</b> <code>{user.balance} ⭐</code>

<b>📦 Оплачено запросов:</b> <code>{user.paid_requests}</code>

<b>💎 Премиум-статус:</b> <code>{user.is_premium}</code>
<b>📅 Действует до:</b> <code>{user.premium_datetime}</code>

<b>🤖 Выбранная модель:</b> <code>{user.last_model}</code>

━━━━━━━━━━━━━━━
<i>Спасибо, что пользуетесь нашим ботом ✨</i>
    """
    return text


@handler_profile.message(F.text == "👤Профиль")
async def profile(message: Message):
    profile_msg = await build_profile_message(message.from_user.id)
    await message.answer(profile_msg, parse_mode="HTML")