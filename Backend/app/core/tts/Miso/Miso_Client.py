"""Miso TTS client — calls a local Miso TTS HTTP server.

MisoTTS requires Python 3.10-3.12 and torch 2.4.0, which are incompatible
with the Backend's Python 3.13 venv. Instead of importing the generator
directly, this client calls a separate HTTP server (server.py in MisoTTS/)
that runs in its own venv.

The client checks availability at startup by hitting the /health endpoint.

Server: Backend/MisoTTS/server.py (port 9100)
Model:  MisoLabs/MisoTTS (8B, loaded by the server)
Output: base64 PCM s16le at the server's sample rate (24000).
"""

from __future__ import annotations

import asyncio
import base64
import os
from typing import AsyncIterator

from app.events import TTSChunkEvent

# Server state — checked by init_pipeline() during app startup.
_available = False
_sample_rate = 24000
_server_url = os.getenv("MISO_SERVER_URL", "http://127.0.0.1:9100")


def init_pipeline() -> None:
    """Check if the Miso TTS server is running. Called once at startup."""
    global _available, _sample_rate
    if _available:
        return
    print(f"[miso] Checking Miso TTS server at {_server_url} ...")
    import urllib.request
    import urllib.error

    try:
        req = urllib.request.Request(f"{_server_url}/health", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                import json
                data = json.loads(resp.read())
                _sample_rate = data.get("sample_rate", 24000)
                _available = True
                print(f"[miso] Server online. Sample rate: {_sample_rate}")
    except Exception as e:
        _available = False
        print(f"[miso] Server not reachable: {e}")
        print("[miso] To start it: cd Backend/MisoTTS && python server.py")


def is_available() -> bool:
    """Check if the Miso TTS server is available."""
    return _available


class MisoTTS:
    """TTS client that calls the Miso TTS HTTP server."""

    def __init__(self, sample_rate: int = 24000):
        self.sample_rate = sample_rate
        self._actual_rate = None
        self._audio_bytes = b""

    async def send_text(self, text: str | None, *, continue_: bool = True) -> None:
        """Synthesize text via the Miso server and buffer the audio."""
        if not text or not text.strip():
            return
        if not _available:
            raise RuntimeError("Miso TTS server is not available")

        loop = asyncio.get_event_loop()
        self._audio_bytes = await loop.run_in_executor(None, _call_server, text)
        self._actual_rate = _sample_rate

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
        """Nothing to close — HTTP is stateless."""
        pass


def _call_server(text: str) -> bytes:
    """Synchronous HTTP call to the Miso server. Runs in a thread."""
    import json
    import urllib.request

    payload = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(
        f"{_server_url}/tts",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
        return base64.b64decode(data["audio"])