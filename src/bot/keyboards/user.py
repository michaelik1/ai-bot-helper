from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
                           InlineKeyboardMarkup, InlineKeyboardButton)

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