import asyncio
import datetime
from typing import Any, AsyncGenerator, Optional
from aiogram.client.session.base import BaseSession
from aiogram.methods.base import TelegramType
from aiogram.methods import TelegramMethod


class MockTelegramSession(BaseSession):
    def __init__(self, delay_ms: int = 0):
        super().__init__()
        self.delay_ms = delay_ms

    async def close(self) -> None:
        return

    async def stream_content(
        self,
        url: str,
        headers: dict[str, Any] | None = None,
        timeout: int = 30,
        chunk_size: int = 65536,
        raise_for_status: bool = True,
    ) -> AsyncGenerator[bytes, None]:
        if False:
            yield b""
        return

    async def make_request(
        self,
        bot: Any,
        method: TelegramMethod[TelegramType],
        timeout: Optional[int] = None,
    ) -> TelegramType:
        if self.delay_ms:
            await asyncio.sleep(self.delay_ms / 1000)
        name = method.__class__.__name__

        def build(result_payload: Any) -> TelegramType:
            returning_type = method.__returning__
            if isinstance(result_payload, (bool, int, float, str)) and returning_type in (bool, int, float, str):
                return result_payload
            return returning_type.model_validate(result_payload, context={"bot": bot})

        if name == "GetMe":
            return build({
                "id": 999999,
                "is_bot": True,
                "first_name": "MockBot",
                "username": "mock_bot",
            })

        if name == "SendMessage":
            chat_id = getattr(method, "chat_id", 0)
            text = getattr(method, "text", "")
            now = int(datetime.datetime.now().timestamp())
            return build({
                "message_id": 1,
                "date": now,
                "chat": {"id": chat_id, "type": "private"},
                "text": text,
            })

        if name in ("EditMessageText", "EditMessageCaption"):
            chat_id = getattr(method, "chat_id", 0)
            text = getattr(method, "text", "") or getattr(method, "caption", "")
            now = int(datetime.datetime.now().timestamp())
            return build({
                "message_id": getattr(method, "message_id", 1),
                "date": now,
                "chat": {"id": chat_id, "type": "private"},
                "text": text,
            })

        if name in ("AnswerCallbackQuery", "SendChatAction", "DeleteMessage"):
            return True

        if name == "GetUpdates":
            return []

        raise NotImplementedError(f"MockTelegramSession: method {name} not implemented")
