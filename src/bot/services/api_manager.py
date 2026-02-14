from src.bot.services.api import NvidiaNIMClient, MODELS
from os import getenv
from asyncio import to_thread
class ApiManager:
    _nv_client: NvidiaNIMClient = None

    @classmethod
    def setup(cls):
        key1 = getenv("NVAPI_KEY1")
        key2 = getenv("NVAPI_KEY2")
        key3 = getenv("NVAPI_KEY3")
        key4 = getenv("NVAPI_KEY4")
        key5 = getenv("NVAPI_KEY5")
        key6 = getenv("NVAPI_KEY6")
        key7 = getenv("NVAPI_KEY7")
        keys = [key1, key2, key3, key4, key5, key6, key7]
        if not keys:
            raise RuntimeError("No NVIDIA API keys found in env (NVAPI_KEY1..NVAPI_KEY7)")
        api_keys = {alias: keys for alias in MODELS.keys()}
        cls._nv_client = NvidiaNIMClient(api_keys)

    @classmethod
    async def send_request(cls, model: str, message: str) -> str:
        if cls._nv_client is None:
            raise RuntimeError("NvidiaNIMClient not initialized. Call ApiManager.setup() first.")
        messages = [
            {"role": "system", "content": "Ты полезный ассистент. Отвечай по-русски."},
            {"role": "user", "content": message},
        ]
        def _call():
            return cls._nv_client.chat_completion(
                model=model,
                messages=messages,
                max_tokens=300,
            )
        resp = await to_thread(_call)
        if isinstance(resp, dict) and resp.get("error"):
            raise RuntimeError(resp["error"])
        return resp["choices"][0]["message"]["content"]
