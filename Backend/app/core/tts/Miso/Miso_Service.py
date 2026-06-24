"""Miso TTS transform: Voice events -> Voice events (with audio).

Same pattern as Cartesia_Service but uses the local MisoTTS client.
Accumulates agent_chunk tokens and, on agent_end, synthesizes via Miso One.
Audio is yielded as TTSChunkEvent chunks.
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import AsyncIterator

from app.core.tts.Miso.Miso_Client import MisoTTS
from app.events import VoiceAgentEvent


async def tts_stream(
    event_stream: AsyncIterator[VoiceAgentEvent],
) -> AsyncIterator[VoiceAgentEvent]:
    tts = MisoTTS()
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

    async def pump_miso():
        try:
            while True:
                async for tts_event in tts.receive_events():
                    await queue.put(tts_event)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Miso TTS error: {e}")
        finally:
            await queue.put(None)

    upstream_task = asyncio.create_task(pump_upstream())
    miso_task = asyncio.create_task(pump_miso())
    sentinels = 0

    try:
        while sentinels < 2:
            event = await queue.get()
            if event is None:
                sentinels += 1
                if sentinels == 1:
                    miso_task.cancel()
                continue
            yield event
    finally:
        upstream_task.cancel()
        miso_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await upstream_task
        with contextlib.suppress(asyncio.CancelledError):
            await miso_task
        await tts.close()