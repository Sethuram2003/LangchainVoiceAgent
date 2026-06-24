"""Miso One TTS client — local inference via the MisoTTS generator.

Miso TTS 8B is NOT a standard transformers pipeline — it uses a custom
generator module from the MisoLabsAI/MisoTTS repository. The model loads
via `generator.load_miso_8b(model_path_or_repo_id="MisoLabs/MisoTTS")`.

Model: MisoLabs/MisoTTS (8B params, Sesame CSM architecture)
Output: torch float32 tensor at generator.sample_rate (24000 Hz).
Requires: torch, torchaudio, and the MisoTTS repo installed.

The generator is loaded once at startup via init_pipeline() (called from
the FastAPI lifespan), not lazily on first use.
"""

from __future__ import annotations

import asyncio
from typing import AsyncIterator

from app.events import TTSChunkEvent

# Pipeline state — populated by init_pipeline() during app startup.
_generator = None
_sample_rate = 24000


def init_pipeline() -> None:
    """Load the Miso TTS 8B model into memory. Called once at startup."""
    global _generator, _sample_rate
    if _generator is not None:
        return
    print("[miso] Loading Miso TTS 8B (MisoLabs/MisoTTS) ...")
    import torch
    from generator import load_miso_8b

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[miso] Using device: {device}")
    _generator = load_miso_8b(
        device=device,
        model_path_or_repo_id="MisoLabs/MisoTTS",
    )
    _sample_rate = _generator.sample_rate
    print(f"[miso] Ready. Sample rate: {_sample_rate}")


def is_available() -> bool:
    """Check if the Miso pipeline has been loaded."""
    return _generator is not None


def _get_generator():
    """Return the loaded generator, or raise if not initialized."""
    if _generator is None:
        raise RuntimeError(
            "Miso pipeline not initialized. Call init_pipeline() at startup. "
            "Install Miso deps: uv sync --extra miso, and clone "
            "https://github.com/MisoLabsAI/MisoTTS into your Python path."
        )
    return _generator, _sample_rate


def _torch_to_pcm16_bytes(audio_tensor) -> bytes:
    """Convert a torch float32 1D tensor to PCM s16le bytes."""
    import numpy as np
    arr = audio_tensor.cpu().numpy().astype(np.float32)
    clipped = np.clip(arr, -1.0, 1.0)
    pcm = (clipped * 32767).astype(np.int16)
    return pcm.tobytes()


class MisoTTS:
    """Local TTS using Miso TTS 8B via the custom generator."""

    def __init__(self, sample_rate: int = 24000):
        self.sample_rate = sample_rate
        self._actual_rate = None
        self._audio_bytes = b""

    async def send_text(self, text: str | None, *, continue_: bool = True) -> None:
        """Synthesize text and buffer the audio. Called on agent_end."""
        if not text or not text.strip():
            return
        gen, rate = _get_generator()
        self._actual_rate = rate

        # Run inference in a thread so we don't block the event loop.
        loop = asyncio.get_event_loop()

        def _generate():
            return gen.generate(
                text=text,
                speaker=0,
                context=[],
                max_audio_length_ms=10_000,
            )

        audio_tensor = await loop.run_in_executor(None, _generate)

        self._audio_bytes = _torch_to_pcm16_bytes(audio_tensor)
        self._actual_rate = rate

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
        """Nothing to close — generator is in-process."""
        pass