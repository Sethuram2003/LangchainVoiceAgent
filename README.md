# LangchainVoiceAgent

Real-time voice agent: **Audio → AssemblyAI STT → Ollama LLM Agent → Cartesia TTS → Audio**

## Structure

```
Backend/    FastAPI WebSocket server (port 8000)
Frontend/   Single-page HTML test client (no build needed)
```

## Quick Start

1. **Backend** — see `Backend/README.md` for details:
   ```bash
   cd Backend
   uv sync
   cp .env.example .env   # fill in ASSEMBLYAI_API_KEY and CARTESIA_API_KEY
   uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. **Frontend** — just open the file in a browser:
   ```
   open Frontend/index.html
   ```
   Click "Start Recording", speak, and watch the pipeline run.