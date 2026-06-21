<div align="center">

# 🎙️ LangChain Voice Agent

### Real-time, speaker-aware voice AI — listens, transcribes, thinks, and talks back.

[![Stars](https://img.shields.io/github/stars/sethuram2003/LangchainVoiceAgent?style=for-the-badge&color=ffd33d)](https://github.com/sethuram2003/LangchainVoiceAgent/stargazers)
[![Forks](https://img.shields.io/github/forks/sethuram2003/LangchainVoiceAgent?style=for-the-badge&color=blue)](https://github.com/sethuram2003/LangchainVoiceAgent/network/members)
[![Issues](https://img.shields.io/github/issues/sethuram2003/LangchainVoiceAgent?style=for-the-badge&color=orange)](https://github.com/sethuram2003/LangchainVoiceAgent/issues)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](#license)

<!-- ⚠️ Badge URLs assume the repo lives at github.com/sethuram2003/LangchainVoiceAgent.
     Swap the path if your repo lives somewhere else. -->

**Built with**

[![Python](https://img.shields.io/badge/Python_3.13-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=flat-square&logo=langchain&logoColor=white)](https://www.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1C3C3C?style=flat-square)](https://www.langchain.com/langgraph)
[![Ollama](https://img.shields.io/badge/Ollama-000000?style=flat-square&logo=ollama&logoColor=white)](https://ollama.com/)
[![AssemblyAI](https://img.shields.io/badge/AssemblyAI-1A1A2E?style=flat-square)](https://www.assemblyai.com/)
[![Cartesia](https://img.shields.io/badge/Cartesia-FF5A5F?style=flat-square)](https://cartesia.ai/)
[![WebSocket](https://img.shields.io/badge/WebSocket-realtime-purple?style=flat-square)](#)
[![uv](https://img.shields.io/badge/uv-package_manager-DE5FE9?style=flat-square)](https://docs.astral.sh/uv/)

</div>

---

```
🎙️ Audio  →  AssemblyAI (STT + Diarization)  →  LangChain Agent (Ollama)  →  Cartesia (TTS)  →  🔊 Audio
```

Speak into the browser client, and within a turn or two you'll hear a natural, low-latency voice response — with the agent automatically noticing **who** is speaking, asking their name once, and using it from then on.

<div align="center">

`real-time` · `streaming-stt` · `speaker-diarization` · `multi-speaker-tracking` · `llm-agent` · `streaming-tts` · `websocket` · `voice-ai` · `langchain-agent` · `local-llm` · `conversational-memory` · `zero-build-frontend`

</div>

---

## 📑 Table of Contents

- [🤔 Why this project](#why-this-project)
- [🏗️ Architecture](#architecture)
- [✨ Core capabilities](#core-capabilities)
- [🔄 Handling multi-speaker calls & handovers](#handling-multi-speaker-calls--handovers)
- [📡 Event protocol](#event-protocol)
- [📁 Project structure](#project-structure)
- [⚙️ Setup](#setup)
- [🔧 Configuration](#configuration)
- [▶️ Running it](#running-it)
- [🔁 How the pipeline streams](#how-the-pipeline-streams)
- [⚠️ Known limitations & edge cases](#known-limitations--edge-cases)
- [🧩 Extending the project](#extending-the-project)
- [🛠️ Troubleshooting](#troubleshooting)
- [📄 License](#license)

---

## 🤔 Why this project

Most "voice agent" demos bolt a single STT → LLM → TTS chain together and call it done. That works for one person, one mic, one continuous conversation. The moment a **second voice joins the call** — a colleague leans in, a customer hands the phone to a manager, someone else picks up — naive pipelines either:

- keep treating every voice as the same person, or
- have no concept of "who" at all, just a flat transcript.

This project is built around the idea that **the agent should track speakers, not just text**. It uses AssemblyAI's real-time diarization to distinguish voices as they speak, and a LangChain agent that's explicitly prompted to learn and remember names per speaker — so a phone-handover mid-call doesn't confuse the conversation.

## 🏗️ Architecture

The backend is a single async generator pipeline. Each stage **consumes an async stream of events and yields an async stream of events**, passing through everything it doesn't touch — so downstream stages always see the full event history, not just their own output.

```
WebSocket (raw PCM16 audio in)
        │
        ▼
┌───────────────────┐
│   stt_stream()     │  AssemblyAI Universal-Streaming v3
│   (AssemblyAI)      │  → STTChunkEvent (partial) / STTOutputEvent (final, diarized)
└───────────────────┘
        │  (passes through + injects)
        ▼
┌───────────────────┐
│   agent_stream()    │  LangChain agent (create_agent) backed by Ollama
│   (LangChain)       │  → AgentChunkEvent (token stream) / AgentEndEvent (full reply)
└───────────────────┘
        │  (passes through + injects)
        ▼
┌───────────────────┐
│   tts_stream()      │  Cartesia WebSocket TTS
│   (Cartesia)         │  → TTSChunkEvent (raw PCM16 audio out)
└───────────────────┘
        │
        ▼
WebSocket (JSON events out, audio chunks base64-encoded)
```

This "stream-of-events, pass-through" design (see `app/events.py` and `app/main.py`) means:

- The frontend gets **every** intermediate event (partial transcripts, final transcripts, streaming agent tokens, final agent text, audio chunks) over one socket — enough to build a fully transparent UI showing the pipeline thinking in real time.
- Each stage is independently swappable. Want Deepgram instead of AssemblyAI, or ElevenLabs instead of Cartesia? Replace one file; the event contract doesn't change.

## ✨ Core capabilities

- **Real-time streaming STT** via AssemblyAI's Universal-Streaming v3 WebSocket API, with partial (`stt_chunk`) and finalized, end-of-turn (`stt_output`) transcripts.
- **Built-in speaker diarization** — AssemblyAI labels each turn with a `speaker_label` (e.g. `A`, `B`, `C`) based on voice characteristics, with no extra setup required (`speaker_labels=true` is requested at connect time).
- **Conversational memory per call** — the agent runs on a `langgraph` `InMemorySaver` checkpointer keyed by a per-connection `thread_id`, so it remembers everything said earlier in *that* call.
- **Name learning and speaker-aware addressing** — the system prompt (`app/core/agent/prompt.py`) instructs the model to detect when a new speaker label appears, ask for their name, and use real names instead of raw labels from then on — across the rest of the conversation.
- **Token-level streaming LLM responses** — agent replies stream token-by-token (`agent_chunk`) as the model generates them, then a final consolidated event (`agent_end`) fires when the turn is complete.
- **Low-latency streaming TTS** via Cartesia's WebSocket API — synthesis starts as soon as a full agent reply is ready, returning raw PCM16 audio chunks (`tts_chunk`) for immediate playback.
- **Single WebSocket, fully event-driven** — one `/ws` endpoint carries audio in and a typed JSON event stream out; no polling, no REST round-trips mid-call.
- **Pluggable local or cloud LLM** — runs against any Ollama-compatible model (defaults to `glm-5.2:cloud`), so you can point it at a fully local model or a hosted one without touching the pipeline code.
- **Zero-build frontend** — `Frontend/index.html` is a dependency-free test client: mic capture, PCM16 downsampling to 16kHz, live partial/final transcript display with per-speaker color coding, streaming agent text, and gapless TTS audio playback, all in vanilla JS.

## 🔄 Handling multi-speaker calls & handovers

This is the interesting edge case, so it's worth explaining precisely **how** it works and **where the line is**.

### The scenario
Person A is on a call with the agent. Partway through, A hands the phone/mic to Person B, who keeps talking without any explicit "hey, it's someone else now" signal in the words themselves.

### How the system handles it

1. **Diarization does the detection.** AssemblyAI's streaming diarization (`speaker_labels=true`) clusters incoming audio by voice characteristics in real time. When B starts speaking, AssemblyAI typically assigns a **new** `speaker_label` (e.g. switches from `A` to `B`) because the acoustic signature of the voice has changed — this happens automatically at the transcription layer, with no involvement from the LLM.
2. **The label rides along with every transcript.** `AssemblyAI_client.py` reads `speaker_label` off each `Turn` message and attaches it to the resulting `STTChunkEvent` / `STTOutputEvent`.
3. **The agent sees the label change.** In `agent.py`, every final transcript is sent to the LLM prefixed with its speaker label: `f"[{speaker}] {transcript}"`. So if the label flips from `A` to `B` mid-call, the very next message the model receives literally starts with `[B]` instead of `[A]`.
4. **The system prompt tells the model what to do about it.** `prompt.py` explicitly instructs the agent to:
   - notice when a new speaker label appears for the first time,
   - politely ask for that person's name,
   - remember the label → name mapping for the rest of the conversation, and
   - address everyone by name going forward, never by raw label, in spoken output.
5. **Conversation memory makes the mapping durable for the call.** Because the agent runs through `create_agent(..., checkpointer=InMemorySaver())` keyed by a single `thread_id` per WebSocket connection, the entire labeled history — including the name the model asked for and was given — stays in context for the rest of that call. So once B says "It's Maria," the agent can say "Got it, Maria" and "Maria, you mentioned..." for the remainder of the session.

In short: **diarization detects the handover, label-prefixing surfaces it to the LLM, and prompting handles the social response** (asking for a name and using it consistently). No part of this requires the user to say "this is someone else now" — the system notices from the voice itself.

### Where this approach has real limits

Be aware of these when relying on it:

- **Per-call only, not cross-call biometric recognition.** The label → name mapping lives in the in-memory LangGraph checkpoint for the lifetime of one `thread_id`. It is **not** a voice-print database — if Maria calls again tomorrow, the agent has no memory of her voice and will ask for her name again. There's no persistent speaker-identity store in this codebase.
- **Diarization can mislabel.** Very similar voices, fast back-and-forth interruptions, phone/codec artifacts, or background noise can cause diarization to mis-cluster speakers (e.g. assign the same label to two different people, or split one person across two labels). The agent's understanding of "who's who" is only as good as AssemblyAI's diarization output.
- **Silent handover with no name ever given.** If B never answers the "what's your name" prompt (e.g. talks past it, or the call ends quickly), the agent will keep referring to them by label internally and may re-ask later — there's no fallback identity beyond the diarization label.
- **State resets on disconnect.** Because `thread_id` is generated fresh per WebSocket connection (`agent_stream` creates a new `uuid.uuid4()` each time `voice_agent_pipeline` runs), reconnecting — even moments later — starts a brand-new memory thread. There's no session resumption built in.

If you need cross-session speaker recognition (e.g. "this is the same Maria as last week's call"), you'd need to add a persistent voice-print/embedding store and identity-matching step — that's a natural extension point, not something this repo currently does.

## 📡 Event protocol

All events are defined in `app/events.py` and serialized to JSON over the WebSocket. Every event includes a `type` and a `ts` (epoch ms).

| Event | Direction | Fields | Meaning |
|---|---|---|---|
| *(raw bytes)* | Client → Server | PCM16, 16kHz, mono | Raw microphone audio chunks |
| `stt_chunk` | Server → Client | `transcript`, `speaker` | Partial (in-progress) transcript for the current turn |
| `stt_output` | Server → Client | `transcript`, `speaker` | Finalized transcript once AssemblyAI marks end-of-turn |
| `agent_chunk` | Server → Client | `text` | One streamed token/fragment of the agent's reply |
| `agent_end` | Server → Client | `text` | The complete agent reply for that turn |
| `tts_chunk` | Server → Client | `audio` (base64 PCM16 @ 24kHz) | A chunk of synthesized speech audio |

The frontend's `handleEvent()` switch statement in `Frontend/index.html` shows a complete reference implementation for consuming this protocol — including gapless audio playback scheduling and per-speaker color-coded transcript rendering.

## 📁 Project structure

```
LangchainVoiceAgent/
├── README.md
├── Backend/
│   ├── .env.example              # Required environment variables
│   ├── .python-version            # Python 3.13
│   └── app/
│       ├── main.py                 # FastAPI app, /ws endpoint, pipeline wiring
│       ├── events.py               # Typed event dataclasses + JSON serialization
│       ├── api/                    # (reserved for REST endpoints)
│       └── core/
│           ├── agent/
│           │   ├── agent.py        # LangChain agent stream transform
│           │   └── prompt.py       # System prompt (speaker-naming logic lives here)
│           ├── stt/AssemblyAI/
│           │   ├── AssemblyAI_client.py   # Low-level AssemblyAI WS client
│           │   └── AssemblyAI_service.py  # audio-in → STT-events-out transform
│           └── tts/Cartesia/
│               ├── Cartesia_Client.py     # Low-level Cartesia WS client
│               └── Cartesia_Service.py    # agent-events-in → audio-events-out transform
└── Frontend/
    └── index.html                  # Zero-build browser test client
```

## ⚙️ Setup

### Prerequisites

- Python 3.13 (see `Backend/.python-version`)
- [`uv`](https://docs.astral.sh/uv/) for dependency management
- An [AssemblyAI](https://www.assemblyai.com/) API key (streaming STT access)
- A [Cartesia](https://cartesia.ai/) API key (streaming TTS access)
- [Ollama](https://ollama.com/) running locally (or any Ollama-compatible endpoint), with your chosen model pulled
- A modern browser with microphone access for the test client

### Install

```bash
cd Backend
uv sync
cp .env.example .env
```

Fill in `.env`:

```bash
ASSEMBLYAI_API_KEY=your_assemblyai_key_here
CARTESIA_API_KEY=your_cartesia_key_here
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=glm-5.2:cloud
ASSEMBLYAI_SPEECH_MODEL=u3-rt-pro
```

## 🔧 Configuration

| Variable | Default | Description |
|---|---|---|
| `ASSEMBLYAI_API_KEY` | *(required)* | API key for AssemblyAI streaming STT |
| `CARTESIA_API_KEY` | *(required)* | API key for Cartesia streaming TTS |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Where the agent's LLM backend is served |
| `OLLAMA_MODEL` | `glm-5.2:cloud` | Model name/tag passed to `ChatOllama` |
| `ASSEMBLYAI_SPEECH_MODEL` | `u3-rt-pro` | AssemblyAI streaming speech model variant |

Other tunables live directly in code rather than env vars:

- **Cartesia voice / model / sample rate** — `CartesiaTTS.__init__` defaults in `Cartesia_Client.py` (`voice_id`, `model_id="sonic-3"`, `sample_rate=24000`).
- **Diarization & turn formatting** — query params in `AssemblyAI_client.py`'s `_ensure_connection` (`speaker_labels=true`, `format_turns=true`).
- **Agent persona / speaker-handling behavior** — edit `app/core/agent/prompt.py` directly.

## ▶️ Running it

**1. Start Ollama and make sure your model is available:**
```bash
ollama pull glm-5.2:cloud   # or whichever model you configured
```

**2. Start the backend:**
```bash
cd Backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**3. Open the frontend:**
```bash
open Frontend/index.html
```

Click **Start Recording**, grant mic permission, and talk. You'll see:
- live partial transcripts as you speak,
- a finalized, speaker-colored transcript once you pause,
- the agent's reply streaming in token by token,
- and finally hear it spoken back through Cartesia TTS.

Have a second person speak into the same mic (or hand off the call) to see diarization assign a new speaker label and watch the agent ask for their name.

## 🔁 How the pipeline streams

The whole system is built on Python async generators chained together (`app/main.py`):

```python
stt_events = stt_stream(audio_stream)      # bytes -> STT events
agent_events = agent_stream(stt_events)    # STT events -> + agent events
tts_events = tts_stream(agent_events)      # agent events -> + audio events
```

Each stage **passes through every event it receives** and *injects* its own new events at the right point — so the final `tts_stream` output contains the entire interleaved history: partial transcripts, final transcripts, streaming tokens, final agent text, and audio chunks, all in original arrival order. This is what lets the frontend render a fully live, transparent view of the pipeline instead of just "audio in, audio out."

`tts_stream` in particular runs two concurrent pumps (upstream events, and Cartesia's audio responses) merged through a shared queue, so audio can start streaming back to the client while later pipeline stages are still doing their own work — minimizing perceived latency.

## ⚠️ Known limitations & edge cases

- **No persistent speaker identity** — see [Handling multi-speaker calls & handovers](#handling-multi-speaker-calls--handovers) above. Identity is per-call, diarization-driven, and memory-only.
- **No tool use configured** — `create_agent(..., tools=[])` is wired up but empty; the agent currently can't browse, calculate, or call external APIs out of the box. Add LangChain tools here to extend it.
- **No authentication on the WebSocket** — `/ws` is open and CORS is wide open (`allow_origins=["*"]`) for local development; lock this down before deploying publicly.
- **ScriptProcessorNode in the frontend** — the demo client uses the deprecated `createScriptProcessor` API for simplicity/compatibility. For production use, migrate to `AudioWorkletNode`.
- **Single LLM turn per final transcript** — the agent reacts once per `stt_output` (end-of-turn). Rapid interruptions or overlapping speech within a single AssemblyAI turn window are resolved by AssemblyAI's turn detection, not by application-level interruption handling.
- **No automatic reconnection** — if the AssemblyAI or Cartesia WebSocket drops mid-call, the current implementation does not automatically retry; the pipeline will surface the resulting error.

## 🧩 Extending the project

Because every stage is a typed async-generator transform over `VoiceAgentEvent`, extension points are clean:

- **Swap STT/TTS providers** — implement a new transform with the same `AsyncIterator[VoiceAgentEvent] -> AsyncIterator[VoiceAgentEvent]` signature and drop it into `main.py`.
- **Add LLM tools** — pass real tools into `create_agent(tools=[...])` in `agent.py` (e.g. search, calendar, CRM lookups) to make the assistant actually *do* things, not just talk.
- **Persistent speaker identity** — swap `InMemorySaver()` for a persistent checkpointer, and add a voice-embedding/identity-matching step ahead of the agent to recognize returning speakers across calls.
- **REST endpoints** — `app/api/` is reserved and currently empty; add routers here for call history, transcripts, or admin endpoints.

## 🛠️ Troubleshooting

| Symptom | Likely cause |
|---|---|
| `ValueError: ASSEMBLYAI_API_KEY is not set` | `.env` missing or not loaded — confirm it's in `Backend/` and `load_dotenv()` ran before client init |
| No audio plays back | Browser autoplay policies may block `AudioContext` until a user gesture; the Start Recording click should satisfy this, but check the browser console |
| Agent never responds | Confirm Ollama is running and `OLLAMA_MODEL` is pulled (`ollama list`) and reachable at `OLLAMA_BASE_URL` |
| Speaker labels don't change between people | Diarization needs distinguishable voice characteristics and enough audio per speaker turn — very short interjections may not get re-labeled reliably |
| Choppy/garbled audio | Confirm the frontend is downsampling to 16kHz PCM16 mono before sending, and that Cartesia's 24kHz output isn't being played at the wrong sample rate |

---

## 📄 License

This project is available under the **MIT License**.

---

## ⭐ Support the project

If this saved you time wiring up a real-time voice pipeline, consider:

- ⭐ **starring the repo** — it's the easiest way to help others find it
- 🍴 **forking it** to build your own variant (cross-call speaker memory, new TTS/STT providers, tool-calling agents)
- 🐛 **opening an issue** for bugs, edge cases, or provider quirks you hit along the way

<div align="center">

**Built with** AssemblyAI · LangChain · LangGraph · Ollama · Cartesia · FastAPI

*A real-time pipeline that doesn't just transcribe a call — it tracks who's actually talking.*

</div>
