from src.bot.services.api import NvidiaNIMClient, MODELS
from os import getenv
from asyncio import to_thread, Lock, sleep as async_sleep

class ApiManager:
    _nv_client: NvidiaNIMClient | None = None
    _is_mock = False
    _mock_delay_ms: int | None = None
    _init_lock = Lock()

    @classmethod
    def setup(cls, mock: bool = False, mock_delay_ms: int = 0):
        cls._is_mock = mock
        cls._mock_delay_ms = mock_delay_ms
        if mock:
            cls._nv_client = None
            return

        keys = getenv("NVAPI_KEYS").strip().split("\n")
        if not keys:
            raise RuntimeError("No NVIDIA API keys found in env (NVAPI_KEYS)")

        api_keys = {alias: keys for alias in MODELS.keys()}
        cls._nv_client = NvidiaNIMClient(api_keys)

    @classmethod
    async def _ensure_init(cls):
        if cls._is_mock:
            return
        if cls._nv_client is not None:
            return

        async with cls._init_lock:
            if cls._nv_client is not None:
                return
            cls.setup(mock=False)

    @classmethod
    async def send_request(cls, model: str, message: str) -> str:
        if cls._is_mock:
            if cls._mock_delay_ms:
                await async_sleep(cls._mock_delay_ms / 1000)
            return f"mock({model}): {message[:50]}"

        await cls._ensure_init()
        if cls._nv_client is None:
            raise RuntimeError("NvidiaNIMClient not initialized")

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

        response = await to_thread(_call)
        if isinstance(response, dict) and response.get("error"):
            raise RuntimeError(response["error"])
        return response["choices"][0]["message"]["content"]
