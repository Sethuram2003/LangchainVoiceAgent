"""LangChain agent transform: STT events -> Agent response events.

Passes through all upstream events. When a final transcript (stt_output)
arrives, sends it to the Ollama-backed LangChain agent and streams back
agent_chunk / agent_end events.
"""

from __future__ import annotations

import os
import uuid
from typing import AsyncIterator

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver

from app.events import AgentChunkEvent, AgentEndEvent, VoiceAgentEvent

load_dotenv()

_OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "glm-5.2:cloud")

# Build the agent once at import time.
_agent = create_agent(
    model=ChatOllama(
        model=_OLLAMA_MODEL,
        base_url=_OLLAMA_BASE_URL,
    ),
    tools=[],
    system_prompt=(
        "You are a helpful voice assistant for a sandwich shop. "
        "You are talking to one or more people over a voice call. "
        "The transcription includes a speaker label (SPEAKER_A, SPEAKER_B, etc.) "
        "for each turn. Use the speaker labels to track who is saying what. "
        "If a new speaker joins mid-conversation, acknowledge them naturally. "
        "Address people by their speaker label when there are multiple speakers. "
        "When there is only one speaker (SPEAKER_A), respond normally without labels. "
        "Be concise and friendly. "
        "Do NOT use emojis, special characters, or markdown. "
        "Your responses will be read by a text-to-speech engine."
    ),
    checkpointer=InMemorySaver(),
)


async def agent_stream(
    event_stream: AsyncIterator[VoiceAgentEvent],
) -> AsyncIterator[VoiceAgentEvent]:
    thread_id = str(uuid.uuid4())
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

    async for event in event_stream:
        # Always pass upstream events through.
        yield event

        # On a final transcript, run the agent and stream tokens.
        if event.type == "stt_output":
            # Prefix the message with the speaker label so the LLM knows
            # who is talking.
            speaker = event.speaker or "UNKNOWN"
            msg_content = f"[{speaker}] {event.transcript}"
            full_text = ""
            async for aevent in _agent.astream_events(
                {"messages": [HumanMessage(content=msg_content)]},
                config,
                version="v2",
            ):
                if aevent["event"] != "on_chat_model_stream":
                    continue
                chunk = aevent["data"].get("chunk")
                token = chunk.content if chunk and chunk.content else ""
                if not token:
                    continue
                full_text += token
                yield AgentChunkEvent.create(token)

            if full_text:
                yield AgentEndEvent.create(full_text)