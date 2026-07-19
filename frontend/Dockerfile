# CARA backend — production image
# Pre-downloads the sentence-transformers embedding model at build time so
# the first real request isn't slow. Voice transcription is handled by
# Groq's hosted Whisper API (not a local model), so no ffmpeg or local
# Whisper download is needed here.

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the sentence-transformers embedding model at build time, so
# the running container doesn't stall on its first request while it fetches
# the model weights.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY . .

# Chroma's persistent store lives here — mount a volume at this path in
# production so indexed documents survive container restarts/redeploys.
ENV CHROMA_PERSIST_DIR=/data/chroma_store
RUN mkdir -p /data/chroma_store

EXPOSE 8000

# No --reload in production: it would re-import this module (and reload the
# embedding model) on every filesystem event, wasting memory and time.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]