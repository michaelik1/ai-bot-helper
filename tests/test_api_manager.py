from src.bot.services.api_manager import ApiManager
from dotenv import load_dotenv
from asyncio import run

def test_api_manager():
    load_dotenv()
    ApiManager.setup()
    model_answer = run(ApiManager.send_request("llama8b", "hello!!!"))
    assert model_answer is not None