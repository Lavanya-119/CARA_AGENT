# CARA — Conversational AI Research Agent

CARA is a full-stack AI agent that chats naturally, decides on its own whether
to answer directly, search your uploaded PDFs, search the live web, or run a
calculation, and supports voice input/output in English, Telugu, Hindi,
Tamil, Malayalam, and Kannada.

> This README covers **local development**. For putting CARA on the
> internet, see **[DEPLOYMENT.md](./DEPLOYMENT.md)** once everything works
> locally.

```
cara/
├── backend/    FastAPI + Groq agent + RAG + voice pipeline
└── frontend/   React + Vite + TanStack Router + Tailwind + shadcn/ui
```

This build has been verified structurally: the backend's FastAPI app, routes,
request/response contracts, and the Calculator tool's safety logic were all
tested (with the heavy ML dependencies mocked, since this authoring
environment has limited disk space and no internet access to Hugging Face).
The frontend was built and type-checked with zero errors, and its dev server
was confirmed to serve the app correctly. **You should still follow the
testing steps below on your own machine before considering it "done"** —
that's the point of testing each piece before wiring up the next.

---

## 1. Prerequisites

Install these before starting:

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10 or 3.11 | 3.12 likely works too, but some ML wheels lag behind new Python releases |
| Node.js | 18+ | 20 LTS recommended |
| ffmpeg | any recent version | required by Whisper to decode audio. **Do not** hardcode a path to it — install it properly and let it sit on your system PATH |
| Groq API key | — | sign up at https://console.groq.com |
| Tavily API key | — | sign up at https://tavily.com |

### Installing ffmpeg

- **macOS (Homebrew):** `brew install ffmpeg`
- **Ubuntu/Debian:** `sudo apt update && sudo apt install ffmpeg`
- **Windows:** download a build from https://www.gyan.dev/ffmpeg/builds/, unzip
  it somewhere permanent (e.g. `C:\ffmpeg`), then add `C:\ffmpeg\bin` to your
  **system** PATH environment variable (Settings → System → About → Advanced
  system settings → Environment Variables). Restart your terminal afterward.
  Do **not** patch `os.environ["PATH"]` inside the Python code — that only
  works on the machine it was written on and breaks for everyone else.

Verify it's installed correctly:
```bash
ffmpeg -version
```

---

## 2. Backend setup

```bash
cd backend
python3 -m venv venv

# macOS/Linux
source venv/bin/activate
# Windows (PowerShell)
venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

**⚠️ This install is heavy.** `openai-whisper` and `sentence-transformers`
both pull in PyTorch, and the full set will download roughly 2-3 GB of
packages. This is normal — budget time and disk space for it.

Create a `.env` file in `backend/`:

```env
GROQ_API_KEY=your_groq_key_here
TAVILY_API_KEY=your_tavily_key_here
GROQ_MODEL=openai/gpt-oss-20b
CORS_ORIGINS=http://localhost:5173,http://localhost:8080
CHROMA_PERSIST_DIR=./chroma_store
WHISPER_MODEL_SIZE=small
```

### Verify the Groq model before relying on it

Groq periodically deprecates models. Before you rely on `openai/gpt-oss-20b`,
confirm it's still listed:

```bash
curl -s https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY" | grep -o '"id":"[^"]*"'
```

If it's no longer listed, pick a currently-active chat model from that
response and update `GROQ_MODEL` in `.env` (and the default in `agent.py`)
accordingly.

### Run the backend

```bash
uvicorn main:app --reload --port 8000
```

The first request that touches Whisper or sentence-transformers will be slow
(models load into memory / download on first use). Subsequent requests are
fast. Note the `--reload` flag is fine for active development, but should be
dropped for anything else — see the comment in `main.py` for why.

### Test each endpoint independently (do this before touching the frontend)

**Health check:**
```bash
curl http://localhost:8000/health
# expect: {"status":"ok"}
```

**Chat (no tools needed):**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is 2+2?"}'
```

**Chat (should trigger WebSearch):**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the latest version of Python?"}'
```

**Upload a PDF:**
```bash
curl -X POST http://localhost:8000/upload-document \
  -F "file=@/path/to/some.pdf"
# expect: {"status":"success","chunks_indexed": <some number>}
```

**Chat grounded in that PDF:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "According to the document I uploaded, what does it say about <topic>?"}'
```

**Voice (needs a real audio file — record one from your phone or the browser
first, or use any short `.webm`/`.wav`/`.mp3` clip):**
```bash
curl -X POST http://localhost:8000/voice \
  -F "file=@/path/to/recording.webm"
```
This returns JSON with `user_said`, `detected_language`, `english_question`,
`answer`, and `audio_base64`. To confirm the audio actually decodes, you can
extract and play it:
```bash
python3 -c "
import json, base64
data = json.load(open('response.json'))
open('out.mp3','wb').write(base64.b64decode(data['audio_base64']))
"
```

Confirm all of the above work before moving to the frontend — it's much
easier to debug the agent/RAG/voice pipeline directly than through the
browser.

---

## 3. Frontend setup

```bash
cd frontend
npm install
```

Create a `.env` file in `frontend/` (a `.env.example` is provided):

```env
VITE_API_URL=http://localhost:8000
```

The `VITE_` prefix is required — Vite will not expose the variable to
client-side code without it.

```bash
npm run dev
```

Vite will print the local URL — confirm which port it actually picked (it
defaults to `5173` in this project's `vite.config.ts`, but will use the next
free port if that one is busy). Whatever port it uses, add it to
`CORS_ORIGINS` in the **backend's** `.env` if it differs from the default.

Open the printed URL in your browser. You'll land on a simple local
"sign-in" screen (name only, no password — see the note on auth below),
then land on `/chat`.

---

## 4. Testing each frontend feature end-to-end

1. **Chat** (`/chat`): type a question, press Enter. You should see your
   message on the right, a typing indicator, then CARA's reply on the left.
   Try a math question, a general knowledge question, and (after uploading a
   PDF) a document-grounded question, to exercise all three tools.
2. **Documents** (`/documents`): drag a PDF onto the drop zone or click to
   browse. You should see an uploading state, then a success entry with the
   chunk count. Go back to Chat and ask something the PDF would answer.
3. **Voice** (`/voice`): click the mic, allow microphone permission when
   prompted, speak a short question (at least 2-3 seconds), click again to
   stop. You'll see "Processing...", then the transcript, CARA's answer, and
   hear it spoken back. Try this in English and in one Indian language to
   confirm the auto-detect → translate → respond → speak loop works
   end-to-end.
   - If you deny microphone permission, you should see a clear on-screen
     error rather than a silent failure.
4. **History** (`/history`): after a few chats, this should list them by
   title, message count, and last-updated time. Clicking one should reopen
   it in Chat with its messages intact.
5. **Settings** (`/settings`): toggle light/dark — it should apply instantly
   and persist across a page reload.

---

## 5. Known simplifications (stated explicitly, as requested)

- **Auth is a mock local session.** There's no password and no server-side
  account system — the "sign-in" screen just stores a name in
  `localStorage`. If you want real authentation (e.g. email/password or
  OAuth), that's a separate, larger addition to `main.py` (sessions/JWTs)
  and the frontend (real login forms, protected routes calling the backend).
- **Chat history is stored client-side in `localStorage`**, not in a backend
  database, since the original spec left this as an explicit choice. It
  works well for a single browser but won't sync across devices. To make it
  cross-device, add a `/history` endpoint backed by SQLite/Postgres and swap
  `useConversations.ts` to call it instead of `localStorage`.
- **The "indexed documents" list on the Documents page is also
  client-side.** The backend's Chroma store is the real source of truth for
  what CARA can retrieve from, but there's no `/documents` list endpoint in
  this build's contract, so the frontend just remembers what *it* uploaded.
  Add a `GET /documents` endpoint if you want a canonical, cross-device list.

---

## 6. Troubleshooting

- **`model_not_found` (404) from Groq** — the model name in `GROQ_MODEL` has
  been deprecated. Re-check `https://api.groq.com/openai/v1/models` and
  update it.
- **CORS errors in the browser console** — the frontend's actual origin
  (check the exact `http://localhost:PORT` Vite printed) isn't in the
  backend's `CORS_ORIGINS`. Update `.env` in `backend/` and restart uvicorn.
- **Voice transcription comes back empty or wrong-language** — this is a
  known Whisper limitation on short/quiet clips, especially for Indian
  languages. Record for at least 2-3 seconds in a quiet room; the frontend
  already rejects clips shorter than that.
- **PDF upload succeeds but chat doesn't seem to use it** — the LLM decides
  autonomously whether a question needs `DocumentSearch`; try rephrasing the
  question to more obviously reference "the document" or "what I uploaded".
- **Uploaded PDF "can't be found" even though it's clearly there** — if the
  file lives in a cloud-synced folder (OneDrive, Google Drive Desktop,
  Dropbox) it may be a placeholder that hasn't downloaded locally yet. Copy
  it to a plain local folder first.

---

## 7. Environment variable reference

**`backend/.env`**

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `GROQ_API_KEY` | yes | — | Groq API authentication |
| `TAVILY_API_KEY` | yes | — | Tavily web search authentication |
| `GROQ_MODEL` | no | `openai/gpt-oss-20b` | which Groq chat model the agent uses |
| `CORS_ORIGINS` | no | `http://localhost:5173,http://localhost:8080` | comma-separated allowed frontend origins |
| `CHROMA_PERSIST_DIR` | no | `./chroma_store` | where the vector store persists on disk |
| `WHISPER_MODEL_SIZE` | no | `small` | Whisper model size for speech-to-text |

**`frontend/.env`**

| Variable | Required | Purpose |
|---|---|---|
| `VITE_API_URL` | yes | base URL of the backend, e.g. `http://localhost:8000` |
