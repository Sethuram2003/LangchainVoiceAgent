"""LangChain agent transform: STT events -> Agent response events.

The agent is initialized once at startup (via init_agent()) and reused
for all WebSocket connections. Each connection gets its own thread_id
for conversation memory isolation.
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

from app.core.agent.prompt import SYSTEM_PROMPT
from app.events import AgentChunkEvent, AgentEndEvent, VoiceAgentEvent

load_dotenv()

_OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "glm-5.2:cloud")

_agent = None


def init_agent() -> None:
    """Create the LangChain agent. Called once during FastAPI lifespan startup."""
    global _agent
    if _agent is not None:
        return
    print(f"[agent] Initializing ChatOllama model={_OLLAMA_MODEL} ...")
    _agent = create_agent(
        model=ChatOllama(
            model=_OLLAMA_MODEL,
            base_url=_OLLAMA_BASE_URL,
        ),
        tools=[],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=InMemorySaver(),
    )
    print("[agent] Ready.")


async def agent_stream(
    event_stream: AsyncIterator[VoiceAgentEvent],
) -> AsyncIterator[VoiceAgentEvent]:
    if _agent is None:
        raise RuntimeError("Agent not initialized. Call init_agent() at startup.")

    thread_id = str(uuid.uuid4())
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

    async for event in event_stream:
        yield event

        if event.type == "stt_output":
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