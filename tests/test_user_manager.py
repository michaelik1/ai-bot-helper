from src.bot.services.user_manager import UserManager
from dotenv import load_dotenv
from os import getenv
from asyncio import run

def test_user_manager():
    load_dotenv()
    admin_id_0 = getenv("ADMINS")[0]
    UserManager.setup()
    user = run(UserManager.get_user(int(admin_id_0)))
    assert user is not None
    assert user.id == admin_id_0

