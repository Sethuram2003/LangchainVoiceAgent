"""STT transform: Audio bytes -> STT events.

Producer-consumer pattern:
  - Producer: pumps audio chunks to AssemblyAI
  - Consumer: yields transcription events from AssemblyAI
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import AsyncIterator

from app.core.stt.AssemblyAI.AssemblyAI_client import AssemblyAISTT
from app.events import VoiceAgentEvent


async def stt_stream(
    audio_stream: AsyncIterator[bytes],
) -> AsyncIterator[VoiceAgentEvent]:
    stt = AssemblyAISTT(sample_rate=16000)

    async def send_audio():
        try:
            async for audio_chunk in audio_stream:
                await stt.send_audio(audio_chunk)
        finally:
            await stt.close()

    send_task = asyncio.create_task(send_audio())

    try:
        async for event in stt.receive_events():
            yield event
    finally:
        send_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await send_task
        await stt.close()