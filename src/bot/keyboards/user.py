from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
                           InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from src.bot.utils.models_list import models_dict

keyboard_default = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👤Профиль"), KeyboardButton(text="🤖Модели")],
        [KeyboardButton(text="🛟Правила и помощь")]
    ],
    resize_keyboard=True
)

keyboard_models = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="LLaMA-8b")],
        [KeyboardButton(text="LLaMA-70b")],
        [KeyboardButton(text="LLaMA-405b")],
        [KeyboardButton(text="Mistral-7b")],
        [KeyboardButton(text="Gemma-7b")],
        [KeyboardButton(text="Arctic")],
        [KeyboardButton(text="Nemotron-340b")],
        [KeyboardButton(text="DeepSeek-v3")],
        [KeyboardButton(text="Phi-3mini")],
        [KeyboardButton(text="Qwen-3coder")],
        [KeyboardButton(text="Kimi-2.5")],
    ]
)

def get_keyboard_models() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for model_name in models_dict.keys():
        builder.add(KeyboardButton(text=model_name))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)