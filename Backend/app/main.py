"""Voice agent backend: STT -> Agent -> TTS pipeline over WebSocket.

Audio bytes -> AssemblyAI STT -> LangChain agent -> TTS -> audio bytes.
Supports pluggable TTS: Cartesia (cloud, streaming) or Miso (local, batch).

All heavy initialization (agent model, TTS pipelines) happens in the FastAPI
lifespan context manager at startup — not on the first WebSocket connection.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from dotenv import load_dotenv
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.core.agent.agent import agent_stream, init_agent
from app.core.stt.AssemblyAI.AssemblyAI_service import stt_stream
from app.events import VoiceAgentEvent, event_to_dict

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialize models. Shutdown: clean up."""
    # --- Agent (always loaded) ---
    init_agent()

    # --- Miso TTS (only if miso extras are installed) ---
    miso_available = False
    try:
        from app.core.tts.Miso.Miso_Client import init_pipeline
        init_pipeline()
        miso_available = True
    except ImportError:
        print("[miso] Not installed — skip. Install with: uv sync --extra miso")
    except Exception as e:
        print(f"[miso] Init failed: {e}")

    # Store availability on app state so the WS endpoint can check.
    app.state.miso_available = miso_available
    print(f"[startup] Miso available: {miso_available}")
    print("[startup] Voice agent backend ready.")

    yield

    # --- Shutdown ---
    print("[shutdown] Voice agent backend stopping.")


app = FastAPI(title="LangChain Voice Agent Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _tts_stream(agent_events, provider: str):
    """Select the TTS transform based on the provider name."""
    if provider == "miso":
        from app.core.tts.Miso.Miso_Service import tts_stream as miso_tts
        return miso_tts(agent_events)
    # Default: Cartesia
    from app.core.tts.Cartesia.Cartesia_Service import tts_stream as cartesia_tts
    return cartesia_tts(agent_events)


async def voice_agent_pipeline(
    audio_stream: AsyncIterator[bytes],
    tts_provider: str = "cartesia",
) -> AsyncIterator[VoiceAgentEvent]:
    """Full pipeline: audio -> STT -> Agent -> TTS -> events."""
    stt_events = stt_stream(audio_stream)
    agent_events = agent_stream(stt_events)
    tts_events = _tts_stream(agent_events, tts_provider)
    async for event in tts_events:
        yield event


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    tts: str = Query("cartesia", description="TTS provider: cartesia or miso"),
) -> None:
    # If the user asked for Miso but it's not available, fall back to Cartesia.
    if tts == "miso" and not getattr(websocket.app.state, "miso_available", False):
        print(f"[ws] Miso not available, falling back to Cartesia.")
        tts = "cartesia"

    await websocket.accept()

    async def websocket_audio_stream() -> AsyncIterator[bytes]:
        while True:
            data = await websocket.receive_bytes()
            yield data

    try:
        async for event in voice_agent_pipeline(websocket_audio_stream(), tts):
            await websocket.send_json(event_to_dict(event))
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        with suppress(RuntimeError):
            await websocket.close()


@app.get("/")
async def health():
    return {
        "status": "ok",
        "pipeline": "stt -> agent -> tts",
        "tts_providers": ["cartesia", "miso"],
        "miso_available": getattr(app.state, "miso_available", False),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)