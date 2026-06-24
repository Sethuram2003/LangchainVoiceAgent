"""Miso One TTS client — local inference via transformers pipeline.

Unlike Cartesia (streaming WebSocket), Miso runs locally via a Hugging Face
transformers pipeline. It generates the full audio in one shot, then we chunk
it into TTSChunkEvent bytes to stay compatible with the event pipeline.

Model: miso-ai/miso-one
Output: numpy float32 array at the model's native sample rate.

The pipeline is loaded once at startup via init_pipeline() (called from the
FastAPI lifespan), not lazily on first use.
"""

from __future__ import annotations

import asyncio
from typing import AsyncIterator

from app.events import TTSChunkEvent

# Pipeline state — populated by init_pipeline() during app startup.
_pipeline = None
_sample_rate = 24000


def init_pipeline() -> None:
    """Load the Miso One model into memory. Called once at startup."""
    global _pipeline, _sample_rate
    if _pipeline is not None:
        return
    print("[miso] Loading Miso One model (miso-ai/miso-one) ...")
    from transformers import pipeline as hf_pipeline
    _pipeline = hf_pipeline("text-to-speech", model="miso-ai/miso-one")
    # Probe the sample rate by running a tiny inference.
    probe = _pipeline("test")
    _sample_rate = probe.get("sampling_rate", 24000)
    print(f"[miso] Ready. Sample rate: {_sample_rate}")


def is_available() -> bool:
    """Check if the Miso pipeline has been loaded."""
    return _pipeline is not None


def _get_pipeline():
    """Return the loaded pipeline, or raise if not initialized."""
    if _pipeline is None:
        raise RuntimeError(
            "Miso pipeline not initialized. Call init_pipeline() at startup "
            "or install Miso deps with: uv sync --extra miso"
        )
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
        self._audio_bytes = b""

    async def send_text(self, text: str | None, *, continue_: bool = True) -> None:
        """Synthesize text and buffer the audio. Called on agent_end."""
        if not text or not text.strip():
            return
        pipe, rate = _get_pipeline()
        self._actual_rate = rate

        # Run inference in a thread so we don't block the event loop.
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, pipe, text)

        audio = result["audio"]
        import numpy as np
        if isinstance(audio, list):
            audio = np.array(audio, dtype=np.float32)
        audio = np.asarray(audio, dtype=np.float32).flatten()

        self._audio_bytes = _float32_to_pcm16_bytes(audio)
        self._actual_rate = result.get("sampling_rate", rate)

    async def receive_events(self) -> AsyncIterator:
        """Yield buffered audio as TTSChunkEvent chunks."""
        if self._audio_bytes:
            chunk_size = (self._actual_rate or self.sample_rate) // 10 * 2
            offset = 0
            while offset < len(self._audio_bytes):
                chunk = self._audio_bytes[offset:offset + chunk_size]
                if chunk:
                    yield TTSChunkEvent.create(chunk, self._actual_rate or self.sample_rate)
                offset += chunk_size
            self._audio_bytes = b""

    async def close(self) -> None:
        """Nothing to close — pipeline is in-process."""
        pass