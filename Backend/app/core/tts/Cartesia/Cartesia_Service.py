"""TTS transform: Voice events -> Voice events (with audio).

Passes through all upstream events. Accumulates agent_chunk tokens and, on
agent_end, sends the complete text to Cartesia for synthesis.
Audio chunks from Cartesia are yielded as they arrive.

Both pumps feed into a single queue. Each pump sends a None sentinel when it
finishes. We stop only when BOTH pumps are done, so Cartesia audio for the
last turn has time to arrive even after the upstream has ended.
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import AsyncIterator

from app.core.tts.Cartesia.Cartesia_Client import CartesiaTTS
from app.events import VoiceAgentEvent


async def tts_stream(
    event_stream: AsyncIterator[VoiceAgentEvent],
) -> AsyncIterator[VoiceAgentEvent]:
    tts = CartesiaTTS()
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

    async def pump_cartesia():
        try:
            while True:
                async for tts_event in tts.receive_events():
                    await queue.put(tts_event)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Cartesia error: {e}")
        finally:
            await queue.put(None)

    upstream_task = asyncio.create_task(pump_upstream())
    cartesia_task = asyncio.create_task(pump_cartesia())
    sentinels = 0

    try:
        while sentinels < 2:
            event = await queue.get()
            if event is None:
                sentinels += 1
                # When upstream finishes, cancel the Cartesia listener so it
                # sends its sentinel and we can exit cleanly.
                if sentinels == 1:
                    cartesia_task.cancel()
                continue
            yield event
    finally:
        upstream_task.cancel()
        cartesia_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await upstream_task
        with contextlib.suppress(asyncio.CancelledError):
            await cartesia_task
        await tts.close()