"""Kokoro TTS transform: Voice events -> Voice events (with audio).

Same pattern as Cartesia_Service but uses the local KokoroTTS client.
Accumulates agent_chunk tokens and, on agent_end, synthesizes via Kokoro.
Audio is yielded as TTSChunkEvent chunks.
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import AsyncIterator

from app.core.tts.Kokoro.Kokoro_Client import KokoroTTS
from app.events import VoiceAgentEvent


async def tts_stream(
    event_stream: AsyncIterator[VoiceAgentEvent],
) -> AsyncIterator[VoiceAgentEvent]:
    tts = KokoroTTS()
    queue: asyncio.Queue[VoiceAgentEvent | None] = asyncio.Queue()
    text_buffer: list[str] = []

    async def pump_upstream():
        try:
            async for event in event_stream:
                await queue.put(event)
                if event.type == "agent_chunk":
                    text_buffer.append(event.text)
                elif event.type == "agent_end":
                    full_text = "".join(text_buffer)
                    text_buffer.clear()
                    await tts.send_text(full_text, continue_=False)
        finally:
            await queue.put(None)

    async def pump_kokoro():
        try:
            while True:
                async for tts_event in tts.receive_events():
                    await queue.put(tts_event)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Kokoro TTS error: {e}")
        finally:
            await queue.put(None)

    upstream_task = asyncio.create_task(pump_upstream())
    kokoro_task = asyncio.create_task(pump_kokoro())
    sentinels = 0

    try:
        while sentinels < 2:
            event = await queue.get()
            if event is None:
                sentinels += 1
                if sentinels == 1:
                    kokoro_task.cancel()
                continue
            yield event
    finally:
        upstream_task.cancel()
        kokoro_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await upstream_task
        with contextlib.suppress(asyncio.CancelledError):
            await kokoro_task
        await tts.close()