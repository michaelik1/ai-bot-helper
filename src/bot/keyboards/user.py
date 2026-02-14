from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
                           InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from src.bot.utils.models_list import models_dict

keyboard_default = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💬Новый чат")],
        [KeyboardButton(text="👤Профиль"), KeyboardButton(text="🤖Модели")],
        [KeyboardButton(text="🛟Правила и помощь")]
    ],
    resize_keyboard=True
)

keyboard_chat = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❌Завершить чат")]
    ],
    resize_keyboard=True
)

def build_keyboard_models(selected_name: str) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for model_name in models_dict.keys():
        button_text = model_name
        if model_name == selected_name:
            button_text = "🔶" + button_text
        builder.add(KeyboardButton(text=button_text))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)