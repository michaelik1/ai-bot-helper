from aiogram.fsm.state import StatesGroup, State

class ModelChoice(StatesGroup):
    model = State()

class Chat(StatesGroup):
    waiting_for_exit = State()