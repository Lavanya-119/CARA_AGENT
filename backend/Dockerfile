# CARA backend — production image
# Includes ffmpeg (required by Whisper) and pre-downloads the embedding
# model at build time so the first real request isn't slow.

FROM python:3.11-slim

# ffmpeg is required by Whisper to decode audio. Installed via apt so it's
# on PATH naturally — no OS-specific path hacks needed in Python code.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the sentence-transformers embedding model and the Whisper
# model at build time, so the running container doesn't stall on its first
# request while it fetches ~500MB-1GB of weights.
ENV WHISPER_MODEL_SIZE=small
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" \
    && python -c "import whisper, os; whisper.load_model(os.getenv('WHISPER_MODEL_SIZE', 'small'))"

COPY . .

# Chroma's persistent store lives here — mount a volume at this path in
# production so indexed documents survive container restarts/redeploys.
ENV CHROMA_PERSIST_DIR=/data/chroma_store
RUN mkdir -p /data/chroma_store

EXPOSE 8000

# No --reload in production: it would re-import this module (and reload
# Whisper/embeddings) on every filesystem event, wasting memory and time.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
