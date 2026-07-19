"""
main.py — CARA FastAPI application.

Endpoints:
  GET  /health            — liveness check
  POST /chat              — text chat, runs the agent loop
  POST /upload-document   — upload + index a PDF for RAG
  POST /voice             — full voice pipeline (STT -> agent -> TTS)

Run with (development only):
    uvicorn main:app --reload --port 8000

Run with (anything beyond active development — see README):
    uvicorn main:app --host 0.0.0.0 --port 8000
"""

import logging
import os
import tempfile

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cara.main")

# Import after load_dotenv() so modules that read env vars at import time see them.
from agent import run_agent  # noqa: E402
from rag_engine import index_pdf  # noqa: E402
from voice import process_voice_query  # noqa: E402

app = FastAPI(title="CARA - Conversational AI Research Agent")

# Comma-separated list in .env, e.g.:
# CORS_ORIGINS=http://localhost:5173,http://localhost:8080,https://cara.example.com
_default_origins = "http://localhost:5173,http://localhost:8080"
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", _default_origins).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str


class UploadResponse(BaseModel):
    status: str
    chunks_indexed: int


class VoiceResponse(BaseModel):
    user_said: str
    detected_language: str
    english_question: str
    answer: str
    audio_base64: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    question = (request.question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="'question' must not be empty.")

    try:
        answer = run_agent(question)
    except RuntimeError as exc:
        # e.g. missing GROQ_API_KEY - a config problem, not a client error
        logger.exception("Agent misconfigured")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Agent run failed")
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}") from exc

    return ChatResponse(answer=answer)


@app.post("/upload-document", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    suffix = ".pdf"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        chunks_indexed = index_pdf(tmp_path)
    except Exception as exc:  # noqa: BLE001
        logger.exception("PDF indexing failed")
        raise HTTPException(status_code=500, detail=f"Failed to index PDF: {exc}") from exc
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return UploadResponse(status="success", chunks_indexed=chunks_indexed)


@app.post("/voice", response_model=VoiceResponse)
async def voice(file: UploadFile = File(...)):
    # Match the temp file extension to the actual format the browser sends
    # (audio/webm via MediaRecorder) rather than assuming .wav, to avoid
    # decode mismatches in Whisper/ffmpeg.
    original_name = file.filename or "recording.webm"
    _, ext = os.path.splitext(original_name)
    if not ext:
        ext = ".webm"

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        result = process_voice_query(tmp_path)
    except ValueError as exc:
        # Transcription came back empty - a client-facing, recoverable error.
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Voice pipeline failed")
        raise HTTPException(status_code=500, detail=f"Voice pipeline error: {exc}") from exc
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return VoiceResponse(**result)


if __name__ == "__main__":
    import uvicorn

    # NOTE: reload=True is intentionally NOT used here — it would cause
    # uvicorn to spawn a reloader process that reimports this module (and
    # therefore reloads the Whisper model) on every file change, which is
    # slow and memory-hungry. Use `uvicorn main:app --reload` from the CLI
    # instead if you specifically want reload during active development.
    uvicorn.run(app, host="0.0.0.0", port=8000)
