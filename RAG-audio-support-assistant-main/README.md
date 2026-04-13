# Audio RAG Support Assistant

A real-time AI support assistant for live technical support.
It captures microphone audio, transcribes speech with Deepgram, and generates context-aware support suggestions using Gemini + local document search.

## What this repository contains

- `main.py` – Flask backend with Socket.IO and HTTP endpoints
- `transcription.py` – Deepgram streaming transcription integration
- `rag_search.py` – vector search with Gemini embeddings and ChromaDB
- `llm_suggestions.py` – Gemini suggestion generation from conversation context
- `sentiment_analysis.py` – sentiment and category analysis
- `ingest_docs.py` – manual ingestion into the vector database
- `audio-rag-ui/` – main Next.js frontend for audio capture and dashboard display
- `frontend/` – legacy / alternate frontend code (not required for the root `npm run dev` flow)

## Requirements

- Python 3.10+
- Node.js 18+ / npm
- `pip install -r requirements.txt`
- `npm install` in the root and `cd audio-rag-ui && npm install`
- Deepgram API key and Google Gemini API key

## Setup

1. Activate Python virtual environment:

```powershell
.\.venv-313\Scripts\Activate.ps1
```

2. Install Python dependencies:

```powershell
pip install -r requirements.txt
```

3. Install frontend dependencies:

```powershell
npm install
cd audio-rag-ui
npm install
cd ..
```

4. Create a root `.env` file with:

```env
DEEPGRAM_API_KEY=<your_deepgram_api_key>
GOOGLE_API_KEY=<your_google_api_key>
```

5. Create `audio-rag-ui/.env.local` with:

```env
NEXT_PUBLIC_WS_URL=http://localhost:5001
NEXT_PUBLIC_API_URL=http://localhost:5001
```

## Run

### Start both backend and frontend together

```powershell
npm run dev:all
```

### Or start backend only

```powershell
npm run dev:backend
```

### Or start frontend only

```powershell
npm run dev:frontend
```

### Service endpoints

- Backend HTTP: `http://localhost:5001`
- Backend health: `http://localhost:5001/health`
- Frontend: `http://localhost:3000`

## How it works

1. Frontend captures microphone audio and sends chunks to the backend.
2. Backend streams audio to Deepgram for real-time transcription.
3. Final transcripts are queued for RAG search and Gemini suggestion generation.
4. The backend returns live transcript updates, sentiment, and AI suggestions to the frontend via WebSocket.

## Important files

- `main.py` – backend server, session manager, WebSocket events
- `transcription.py` – Deepgram audio streaming client
- `rag_search.py` – document search with embeddings
- `llm_suggestions.py` – composition of AI suggestion output
- `sentiment_analysis.py` – sentiment and category normalization
- `ingest_docs.py` – ingest `data/manuals/` into the vector database
- `audio-rag-ui/` – Next.js frontend that connects to the backend

## Notes

- The root package script `dev` runs the frontend only.
- Use `dev:all` to run both backend and frontend concurrently.
- The backend expects `DEEPGRAM_API_KEY` and `GOOGLE_API_KEY` in `.env`.
- Ensure `audio-rag-ui/.env.local` points to `http://localhost:5001`.
- `logs/sessions/` contains transcript and suggestion logs.
- Run `python ingest_docs.py --input data/manuals/` before using RAG if you need document search.

## Cleanup

Extra documentation files have been consolidated into this single README.

## Suggested repo name

`audio-rag-support-assistant`

