# LangChain Voice Agent Backend

Real-time voice agent pipeline: **Audio → AssemblyAI STT → LangChain Agent (Ollama) → Cartesia TTS → Audio**

## Architecture

```
Client (WebSocket) --audio bytes--> /ws endpoint
  │
  ├── stt_stream()       AssemblyAI Universal-Streaming v3 → STTChunkEvent / STTOutputEvent
  ├── agent_stream()     LangChain create_agent + ChatOllama → AgentChunkEvent / AgentEndEvent
  └── tts_stream()       Cartesia TTS WebSocket → TTSChunkEvent (audio bytes)
```

All three stages are async generators chained together. Events flow through and
are sent to the client as JSON over the same WebSocket.

## Setup

```bash
# Install deps
uv sync

# Configure environment
cp .env.example .env
# Fill in ASSEMBLYAI_API_KEY and CARTESIA_API_KEY
# OLLAMA_MODEL defaults to glm-5.2:cloud (change to any model in `ollama list`)
```

## Run

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Connect a WebSocket client to `ws://localhost:8000/ws` and start sending 16kHz
PCM audio bytes. You'll receive JSON events:

| Event          | Fields                    | Description                      |
|----------------|---------------------------|----------------------------------|
| `stt_chunk`    | `transcript`              | Partial transcription            |
| `stt_output`   | `transcript`              | Final transcription (end of turn)|
| `agent_chunk`  | `text`                    | Streaming agent token            |
| `agent_end`    | `text`                    | Complete agent response          |
| `tts_chunk`    | `audio` (base64 PCM)      | Synthesized audio chunk          |

## Project Structure

```
app/
├── main.py                              FastAPI app + WebSocket endpoint
├── events.py                            Event dataclasses + serializer
├── core/
│   ├── agent/agent.py                   LangChain agent (Ollama) transform
│   ├── stt/AssemblyAI/
│   │   ├── AssemblyAI_client.py         AssemblyAI WebSocket client
│   │   └── AssemblyAI_service.py        STT transform (audio → events)
│   └── tts/Cartesia/
│       ├── Cartesia_Client.py           Cartesia WebSocket client
│       └── Cartesia_Service.py          TTS transform (events → audio)
```

## Requirements

- Python 3.13+
- Ollama running locally (or use cloud models like `glm-5.2:cloud`)
- AssemblyAI API key
- Cartesia API key