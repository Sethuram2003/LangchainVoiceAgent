"""Cartesia TTS WebSocket client.

Sends text chunks and yields base64-decoded PCM audio chunks.
"""

from __future__ import annotations

import base64
import json
import os
import uuid
from typing import AsyncIterator

import websockets
from dotenv import load_dotenv
from websockets import WebSocketClientProtocol

from app.events import TTSChunkEvent

load_dotenv()


class CartesiaTTS:
    def __init__(
        self,
        api_key: str | None = None,
        voice_id: str = "f6ff7c0c-e396-40a9-a70b-f7607edb6937",
        model_id: str = "sonic-3",
        sample_rate: int = 24000,
        encoding: str = "pcm_s16le",
        language: str = "en",
        cartesia_version: str = "2026-03-01",
    ):
        self.api_key = api_key or os.getenv("CARTESIA_API_KEY")
        if not self.api_key:
            raise ValueError("CARTESIA_API_KEY is not set")
        self.voice_id = voice_id
        self.model_id = model_id
        self.sample_rate = sample_rate
        self.encoding = encoding
        self.language = language
        self.cartesia_version = cartesia_version
        self._ws: WebSocketClientProtocol | None = None
        self._context_counter = 0

    async def send_text(self, text: str | None, *, continue_: bool = True) -> None:
        if not text or not text.strip():
            return
        ws = await self._ensure_connection()
        self._context_counter += 1
        payload = {
            "model_id": self.model_id,
            "transcript": text,
            "voice": {"mode": "id", "id": self.voice_id},
            "output_format": {
                "container": "raw",
                "encoding": self.encoding,
                "sample_rate": self.sample_rate,
            },
            "language": self.language,
            "context_id": str(uuid.uuid4()),
            "continue": continue_,
        }
        await ws.send(json.dumps(payload))

    async def receive_events(self) -> AsyncIterator:
        """Yield audio chunks for ONE generation, until 'done' is received."""
        ws = await self._ensure_connection()
        async for raw_message in ws:
            message = json.loads(raw_message)
            msg_type = message.get("type")

            if msg_type == "chunk" and message.get("data"):
                audio = base64.b64decode(message["data"])
                if audio:
                    yield TTSChunkEvent.create(audio)
            elif msg_type == "done":
                return
            elif msg_type == "error":
                raise RuntimeError(f"Cartesia error: {message.get('message')}")

    async def _ensure_connection(self) -> WebSocketClientProtocol:
        if self._ws is None:
            url = (
                f"wss://api.cartesia.ai/tts/websocket"
                f"?api_key={self.api_key}&cartesia_version={self.cartesia_version}"
            )
            self._ws = await websockets.connect(url)
        return self._ws

    async def close(self) -> None:
        if self._ws is not None:
            await self._ws.close()
            self._ws = None