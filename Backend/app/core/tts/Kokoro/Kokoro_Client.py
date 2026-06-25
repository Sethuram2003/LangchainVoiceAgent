"""Local Kokoro TTS client.

Synthesizes text on-device and yields int16 PCM chunks.
Follows the same send/receive pattern as CartesiaTTS.
"""

from __future__ import annotations

import asyncio
from typing import AsyncIterator

import numpy as np
from kokoro import KPipeline

from app.events import TTSChunkEvent

_pipeline = None

def _get_pipeline() -> KPipeline:
    """Lazy-load the Kokoro pipeline (CPU-friendly, real-time)."""
    global _pipeline
    if _pipeline is None:
        _pipeline = KPipeline(lang_code="a")
    return _pipeline


class KokoroTTS:
    """Local Kokoro TTS client. Synthesizes on-device and yields PCM chunks."""

    def __init__(self, sample_rate: int = 24000, voice: str = "af_bella"):
        self.sample_rate = sample_rate
        self.voice = voice
        self._pcm_bytes = b""
        self._ready = asyncio.Event()

    async def send_text(self, text: str | None, *, continue_: bool = True) -> None:
        """Synthesize text locally and signal that audio is ready."""
        if not text or not text.strip():
            return

        self._ready.clear()
        loop = asyncio.get_event_loop()
        self._pcm_bytes = await loop.run_in_executor(
            None, self._synthesize, text.strip()
        )
        self._ready.set()

    def _synthesize(self, text: str) -> bytes:
        """Blocking call that runs the Kokoro pipeline and returns int16 PCM."""
        pipeline = _get_pipeline()
        chunks = []

        for _, _, audio in pipeline(text, voice=self.voice, speed=1.0):
            chunks.append(audio)

        if not chunks:
            return b""

        full_audio = np.concatenate(chunks)
        int16_audio = (full_audio * 32767).astype(np.int16)
        return int16_audio.tobytes()

    async def receive_events(self) -> AsyncIterator:
        """Yield audio chunks for ONE generation, then return."""
        await self._ready.wait()

        if not self._pcm_bytes:
            return

        chunk_size = self.sample_rate // 10 * 2
        offset = 0
        while offset < len(self._pcm_bytes):
            chunk = self._pcm_bytes[offset:offset + chunk_size]
            if chunk:
                yield TTSChunkEvent.create(chunk, self.sample_rate)
            offset += chunk_size

        self._pcm_bytes = b""
        self._ready.clear()

    async def close(self) -> None:
        """Nothing to close — local inference is stateless."""
        pass