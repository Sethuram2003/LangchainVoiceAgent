"""Miso One TTS client — local inference via transformers pipeline.

Unlike Cartesia (streaming WebSocket), Miso runs locally via a Hugging Face
transformers pipeline. It generates the full audio in one shot, then we chunk
it into TTSChunkEvent bytes to stay compatible with the event pipeline.

Model: miso-ai/miso-one
Output: numpy float32 array at the model's native sample rate.
"""

from __future__ import annotations

import asyncio
import io
import struct
from typing import AsyncIterator

from app.events import TTSChunkEvent

# Lazy-loaded pipeline — torch + transformers are heavy, only import when used.
_pipeline = None
_sample_rate = 24000  # Miso One default; updated after first inference.


def _get_pipeline():
    """Lazily load the transformers text-to-speech pipeline."""
    global _pipeline, _sample_rate
    if _pipeline is None:
        from transformers import pipeline as hf_pipeline
        _pipeline = hf_pipeline("text-to-speech", model="miso-ai/miso-one")
        # Probe the sample rate by running a tiny inference.
        probe = _pipeline("test")
        _sample_rate = probe.get("sampling_rate", 24000)
    return _pipeline, _sample_rate


def _float32_to_pcm16_bytes(samples) -> bytes:
    """Convert a numpy float32 array to PCM s16le bytes."""
    import numpy as np
    clipped = np.clip(samples, -1.0, 1.0)
    pcm = (clipped * 32767).astype(np.int16)
    return pcm.tobytes()


class MisoTTS:
    """Local TTS using Miso One via transformers pipeline."""

    def __init__(self, sample_rate: int = 24000):
        self.sample_rate = sample_rate
        self._actual_rate = None

    async def send_text(self, text: str | None, *, continue_: bool = True) -> None:
        """Synthesize text and buffer the audio. Called on agent_end."""
        if not text or not text.strip():
            return
        pipe, rate = _get_pipeline()
        self._actual_rate = rate

        # Run inference in a thread so we don't block the event loop.
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, pipe, text)

        # result is a dict: {"audio": np.array, "sampling_rate": int}
        audio = result["audio"]
        # Some pipeline versions return a nested list; flatten to 1D.
        import numpy as np
        if isinstance(audio, list):
            audio = np.array(audio, dtype=np.float32)
        audio = np.asarray(audio, dtype=np.float32).flatten()

        self._audio_bytes = _float32_to_pcm16_bytes(audio)
        self._actual_rate = result.get("sampling_rate", rate)

    async def receive_events(self) -> AsyncIterator:
        """Yield buffered audio as a single TTSChunkEvent."""
        audio_bytes = getattr(self, "_audio_bytes", b"")
        if audio_bytes:
            # Send in ~100ms chunks (sample_rate / 10 * 2 bytes per sample).
            chunk_size = (self._actual_rate or self.sample_rate) // 10 * 2
            offset = 0
            while offset < len(audio_bytes):
                chunk = audio_bytes[offset:offset + chunk_size]
                if chunk:
                    yield TTSChunkEvent.create(chunk, self._actual_rate or self.sample_rate)
                offset += chunk_size
            self._audio_bytes = b""

    async def close(self) -> None:
        """Nothing to close — pipeline is in-process."""
        pass

    @property
    def output_sample_rate(self) -> int:
        """The actual sample rate of the generated audio."""
        return self._actual_rate or self.sample_rate