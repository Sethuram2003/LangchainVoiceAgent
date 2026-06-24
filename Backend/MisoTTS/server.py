"""Miso TTS local server — exposes the Miso TTS 8B model over a simple HTTP API.

Run this in a Python 3.10-3.12 venv with the MisoTTS deps installed:
    cd Backend/MisoTTS
    uv venv --python 3.10
    source .venv/bin/activate
    uv pip install -e .
    uv pip install fastapi uvicorn python-multipart
    python server.py

The server loads the model at startup and exposes:
    POST /tts  {"text": "..."}  ->  {"audio": "<base64 pcm s16le>", "sample_rate": 24000}
    GET  /health              ->  {"status": "ok"}
"""

import base64
import os

os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "60")
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "60")
os.environ["NO_TORCH_COMPILE"] = "1"

import numpy as np
import torch
import torchaudio  # noqa: F401
from generator import DEFAULT_MISO_TTS_REPO_ID, load_miso_8b
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Miso TTS Local Server")

# Load model at startup.
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"[miso-server] Using device: {device}")

model_source = os.environ.get("MISO_TTS_8B_MODEL", DEFAULT_MISO_TTS_REPO_ID)
print(f"[miso-server] Loading model: {model_source}")
_generator = load_miso_8b(device, model_path_or_repo_id=model_source)
_sample_rate = _generator.sample_rate
print(f"[miso-server] Ready. Sample rate: {_sample_rate}")


class TTSRequest(BaseModel):
    text: str
    speaker: int = 0
    max_audio_length_ms: int = 10000


class TTSResponse(BaseModel):
    audio: str  # base64-encoded PCM s16le
    sample_rate: int


@app.get("/health")
async def health():
    return {"status": "ok", "sample_rate": _sample_rate}


@app.post("/tts", response_model=TTSResponse)
async def tts(req: TTSRequest):
    audio_tensor = _generator.generate(
        text=req.text,
        speaker=req.speaker,
        context=[],
        max_audio_length_ms=req.max_audio_length_ms,
    )
    # Convert torch tensor -> numpy float32 -> PCM s16le bytes -> base64
    arr = audio_tensor.cpu().numpy().astype(np.float32)
    clipped = np.clip(arr, -1.0, 1.0)
    pcm = (clipped * 32767).astype(np.int16)
    audio_b64 = base64.b64encode(pcm.tobytes()).decode("ascii")
    return TTSResponse(audio=audio_b64, sample_rate=_sample_rate)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9100)