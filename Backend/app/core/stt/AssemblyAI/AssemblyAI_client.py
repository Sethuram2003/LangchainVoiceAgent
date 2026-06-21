"""AssemblyAI Universal-Streaming v3 WebSocket client.

Sends raw PCM audio bytes and yields STT events (partial / final transcripts).
"""

from __future__ import annotations

import json
import os
from typing import AsyncIterator

import websockets
from dotenv import load_dotenv
from websockets import WebSocketClientProtocol

from app.events import STTChunkEvent, STTOutputEvent

load_dotenv()


class AssemblyAISTT:
    def __init__(
        self,
        api_key: str | None = None,
        sample_rate: int = 16000,
        speech_model: str = "u3-rt-pro",
    ):
        self.api_key = api_key or os.getenv("ASSEMBLYAI_API_KEY")
        if not self.api_key:
            raise ValueError("ASSEMBLYAI_API_KEY is not set")
        self.sample_rate = sample_rate
        self.speech_model = speech_model
        self._ws: WebSocketClientProtocol | None = None

    async def send_audio(self, audio_chunk: bytes) -> None:
        ws = await self._ensure_connection()
        await ws.send(audio_chunk)

    async def receive_events(self) -> AsyncIterator:
        ws = await self._ensure_connection()
        async for raw_message in ws:
            message = json.loads(raw_message)
            msg_type = message.get("type")

            if msg_type == "Turn":
                transcript = message.get("transcript", "")
                if not transcript.strip():
                    continue
                speaker = message.get("speaker_label", "UNKNOWN") or "UNKNOWN"
                if message.get("end_of_turn"):
                    yield STTOutputEvent.create(transcript, speaker)
                else:
                    yield STTChunkEvent.create(transcript, speaker)

    async def _ensure_connection(self) -> WebSocketClientProtocol:
        if self._ws is None:
            url = (
                f"wss://streaming.assemblyai.com/v3/ws"
                f"?sample_rate={self.sample_rate}"
                f"&speech_model={self.speech_model}"
                f"&format_turns=true"
                f"&speaker_labels=true"
            )
            self._ws = await websockets.connect(
                url,
                additional_headers={"Authorization": self.api_key or ""},
            )
        return self._ws

    async def close(self) -> None:
        if self._ws is not None:
            await self._ws.close()
            self._ws = None