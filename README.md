## Rescue AI

Backend for an AI-powered emergency helpline (1122/911). Incoming calls are handled by a voice agent that speaks Pakistani Urdu, collects emergency details, and routes to the appropriate service.

## How it works

A caller connects via WebSocket. The backend creates a LiveKit room, dispatches the AI voice agent into it, and returns a token to the client. The agent conducts the conversation in Urdu using Deepgram for speech recognition, Gemini for reasoning, and UpliftAI for TTS. Call sessions are persisted in a Supabase PostgreSQL database.

## Stack

- FastAPI + SQLAlchemy (Supabase/Postgres)
- LiveKit for real-time audio rooms
- LiveKit Agents with Deepgram STT, Google Gemini LLM, UpliftAI TTS
- JWT auth for the dispatcher dashboard

## Setup


Install dependencies and run:

```bash
uv sync
uvicorn app.main:app --reload
```

Run the voice agent worker separately:

```bash
python app/voice/agent.py start
```

## First-time setup

Create the dispatcher user by hitting this endpoint once after the server starts:

```
POST /auth/setup-dispatcher
```

Default credentials: `dispatcher / rescue1122` — change these before going to production.

## API

- `POST /auth/login` — get a JWT token
- `GET /calls/` — list active call sessions (auth required)
- `WS /ws/call` — WebSocket endpoint for incoming calls
