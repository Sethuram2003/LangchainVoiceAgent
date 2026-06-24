"""Voice agent event types.

Typed events that flow through the STT → Agent → TTS pipeline.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Literal, Union


def _now_ms() -> int:
    import time

    return int(time.time() * 1000)


@dataclass
class UserInputEvent:
    """Raw audio from the client."""

    type: Literal["user_input"]
    audio: bytes
    ts: int

    @classmethod
    def create(cls, audio: bytes) -> "UserInputEvent":
        return cls(type="user_input", audio=audio, ts=_now_ms())


@dataclass
class STTChunkEvent:
    """Partial transcription from STT."""

    type: Literal["stt_chunk"]
    transcript: str
    speaker: str
    ts: int

    @classmethod
    def create(cls, transcript: str, speaker: str = "UNKNOWN") -> "STTChunkEvent":
        return cls(type="stt_chunk", transcript=transcript, speaker=speaker, ts=_now_ms())


@dataclass
class STTOutputEvent:
    """Final transcription for a turn."""

    type: Literal["stt_output"]
    transcript: str
    speaker: str
    ts: int

    @classmethod
    def create(cls, transcript: str, speaker: str = "UNKNOWN") -> "STTOutputEvent":
        return cls(type="stt_output", transcript=transcript, speaker=speaker, ts=_now_ms())


STTEvent = Union[STTChunkEvent, STTOutputEvent]


@dataclass
class AgentChunkEvent:
    """Partial text from the agent."""

    type: Literal["agent_chunk"]
    text: str
    ts: int

    @classmethod
    def create(cls, text: str) -> "AgentChunkEvent":
        return cls(type="agent_chunk", text=text, ts=_now_ms())


@dataclass
class AgentEndEvent:
    """Agent finished generating a response."""

    type: Literal["agent_end"]
    text: str
    ts: int

    @classmethod
    def create(cls, text: str) -> "AgentEndEvent":
        return cls(type="agent_end", text=text, ts=_now_ms())


AgentEvent = Union[AgentChunkEvent, AgentEndEvent]


@dataclass
class TTSChunkEvent:
    """Synthesized audio chunk."""

    type: Literal["tts_chunk"]
    audio: bytes
    sample_rate: int
    ts: int

    @classmethod
    def create(cls, audio: bytes, sample_rate: int = 24000) -> "TTSChunkEvent":
        return cls(type="tts_chunk", audio=audio, sample_rate=sample_rate, ts=_now_ms())


VoiceAgentEvent = Union[UserInputEvent, STTEvent, AgentEvent, TTSChunkEvent]


def event_to_dict(event: VoiceAgentEvent) -> dict:
    """Serialize an event for the WebSocket client."""
    if isinstance(event, UserInputEvent):
        audio_b64 = base64.b64encode(event.audio).decode("ascii")
        return {"type": event.type, "audio": audio_b64, "ts": event.ts}
    if isinstance(event, STTChunkEvent):
        return {"type": event.type, "transcript": event.transcript, "speaker": event.speaker, "ts": event.ts}
    if isinstance(event, STTOutputEvent):
        return {"type": event.type, "transcript": event.transcript, "speaker": event.speaker, "ts": event.ts}
    if isinstance(event, AgentChunkEvent):
        return {"type": event.type, "text": event.text, "ts": event.ts}
    if isinstance(event, AgentEndEvent):
        return {"type": event.type, "text": event.text, "ts": event.ts}
    if isinstance(event, TTSChunkEvent):
        audio_b64 = base64.b64encode(event.audio).decode("ascii")
        return {"type": event.type, "audio": audio_b64, "sample_rate": event.sample_rate, "ts": event.ts}
    raise ValueError(f"Unknown event type: {type(event)}")
