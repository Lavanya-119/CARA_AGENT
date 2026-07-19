# Deploying CARA

This covers taking CARA from "running on localhost" to "running on the
internet." Read the **before you deploy** section first — a couple of
CARA's pieces (Whisper, the Chroma vector store) have real implications for
where and how you host it.

---

## 0. Before you deploy — things that matter for hosting

- **The backend is not lightweight.** Whisper (`small`) and the
  sentence-transformers embedding model both load into memory and both
  need real CPU to run inference at acceptable speed. Free-tier serverless
  platforms (e.g. Vercel/Netlify functions) are **not** a fit for the
  backend — they're built for short, stateless requests, not multi-hundred-MB
  models sitting warm in memory. Plan for at least 2 vCPUs / 2-4 GB RAM.
- **The Chroma vector store needs a persistent disk**, not ephemeral
  container storage. If your host wipes the filesystem on every deploy or
  restart (many "serverless container" platforms do), every uploaded PDF
  will vanish. Use a platform with a mountable persistent volume, or migrate
  to a hosted vector DB (e.g. Chroma Cloud, Pinecone, Qdrant Cloud) if you
  need serverless-style deploys.
- **Microphone access requires HTTPS in production.** Browsers block
  `getUserMedia` (what the Voice page uses) on plain HTTP except on
  `localhost`. Any real deployment needs TLS — every option below gives you
  this by default.
- **The frontend is a static SPA** and is the easy part — deploy it anywhere
  that serves static files (Vercel, Netlify, Cloudflare Pages, S3+CloudFront,
  or your own nginx).
- **Groq and Tavily calls happen server-side only** — your API keys never
  reach the browser, which is correct and don't change that.

Given the above, the realistic options are:

| Option | Backend fit | Effort | Cost |
|---|---|---|---|
| A. Render / Railway / Fly.io (Docker + persistent volume) | Good | Low-medium | Paid tier likely needed for enough RAM |
| B. Your own VPS (DigitalOcean, Hetzner, Linode, AWS EC2) with Docker | Best | Medium | Cheapest for 24/7 use |
| C. Serverless platforms (Vercel/Netlify functions, AWS Lambda) | Poor fit | — | Not recommended for this backend |

Frontend, in all cases: Vercel, Netlify, or Cloudflare Pages (Option D below).

---

## Option A — Render, Railway, or Fly.io (Docker + volume)

These platforms all do roughly the same thing: build your `Dockerfile`,
run the container, and let you attach a persistent volume. Steps are
similar across all three; Render is used here as the concrete example.

1. Push this project to a GitHub repo (or GitLab/Bitbucket).
2. On Render: **New → Web Service**, connect the repo, set:
   - **Root directory:** `backend`
   - **Runtime:** Docker (Render will detect the `Dockerfile`)
   - **Instance type:** at least 2 GB RAM (Whisper + embeddings need it)
3. Add a **persistent disk**, mounted at `/data`, sized a few GB. This is
   what `CHROMA_PERSIST_DIR=/data/chroma_store` (already set in the
   Dockerfile) will write into.
4. Add environment variables in Render's dashboard:
   ```
   GROQ_API_KEY=...
   TAVILY_API_KEY=...
   GROQ_MODEL=openai/gpt-oss-20b
   CORS_ORIGINS=https://your-frontend-domain.com
   ```
   (`CHROMA_PERSIST_DIR` and `WHISPER_MODEL_SIZE` already have sane defaults
   baked into the Dockerfile — override only if you need to.)
5. Deploy. Render gives you a public HTTPS URL like
   `https://cara-backend.onrender.com` — that's your `VITE_API_URL` for the
   frontend.
6. Test it exactly like you did locally:
   ```bash
   curl https://cara-backend.onrender.com/health
   ```

Railway and Fly.io follow the same shape: connect the repo or push the
image, attach a volume at the same path, set the same env vars, use their
generated HTTPS URL.

---

## Option B — Your own VPS with Docker (cheapest for always-on use)

1. Spin up a VPS (2 vCPU / 4 GB RAM is a comfortable minimum) — Ubuntu
   22.04/24.04 is a safe default image.
2. SSH in and install Docker:
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   # log out and back in
   ```
3. Copy this project onto the server (`git clone` or `scp`).
4. Create `backend/.env` on the server with your real keys and
   `CORS_ORIGINS` set to your eventual frontend domain.
5. From the project root:
   ```bash
   docker compose up -d --build
   ```
   This builds the backend image and starts it with a named volume
   (`chroma_data`) for persistence, per `docker-compose.yml`.
6. Put a reverse proxy in front of it for HTTPS. The simplest path is
   [Caddy](https://caddyserver.com/), which handles Let's Encrypt certs
   automatically:
   ```bash
   sudo apt install -y caddy
   ```
   `/etc/caddy/Caddyfile`:
   ```
   api.yourdomain.com {
       reverse_proxy localhost:8000
   }
   ```
   ```bash
   sudo systemctl reload caddy
   ```
   Now `https://api.yourdomain.com` proxies to your backend container with
   a valid TLS cert, no manual certificate wrangling.
7. Point your domain's DNS `A` record at the server's IP before the Caddy
   step (it needs to resolve for Let's Encrypt's HTTP challenge to work).
8. Test: `curl https://api.yourdomain.com/health`.

---

## Option C — Why not serverless functions

Vercel/Netlify functions and AWS Lambda cold-start a new process per
invocation (or per short-lived pool) with tight memory/time limits. Loading
Whisper (`small`, ~500MB) and the embedding model on every cold start would
be slow and often exceed the platform's memory ceiling on free/hobby tiers.
If you want a serverless-shaped deploy anyway, you'd need to: split Whisper
transcription out to a dedicated, always-warm service; move Chroma to a
hosted vector DB; and keep only the thin agent-orchestration logic
serverless. That's a meaningfully different architecture from what's built
here — worth doing only if request volume is very spiky and cost-sensitive.

---

## Option D — Deploying the frontend (do this after the backend is live)

The frontend needs your **real backend URL** baked in at build time, so
deploy the backend first.

### Vercel (recommended, simplest)
1. Push the repo to GitHub.
2. On Vercel: **New Project**, import the repo, set:
   - **Root directory:** `frontend`
   - **Framework preset:** Vite
3. Add an environment variable: `VITE_API_URL` = your backend's HTTPS URL
   (e.g. `https://api.yourdomain.com` or the Render URL from Option A).
4. Deploy. Vercel builds and serves the static `dist/` output automatically,
   with HTTPS out of the box.

### Netlify
Same shape as Vercel: root directory `frontend`, build command
`npm run build`, publish directory `dist`, environment variable
`VITE_API_URL` set in the Netlify dashboard before building.

### Cloudflare Pages
Same shape again: root directory `frontend`, build command `npm run build`,
output directory `dist`, environment variable `VITE_API_URL`.

### Self-hosting the frontend too (same VPS as the backend)
Use `frontend/Dockerfile`, which builds the Vite app and serves it via
nginx with SPA-friendly routing already configured:
```bash
cd frontend
docker build --build-arg VITE_API_URL=https://api.yourdomain.com -t cara-frontend .
docker run -d -p 8080:80 --name cara-frontend cara-frontend
```
Then add a second Caddy site block:
```
app.yourdomain.com {
    reverse_proxy localhost:8080
}
```
**Remember:** `VITE_API_URL` is a *build-time* argument here, not a runtime
environment variable — if the backend URL changes, you must rebuild this
image, not just restart the container.

---

## 5. After deploying — close the loop

1. **Update backend CORS** to the frontend's real domain (not `localhost`):
   ```
   CORS_ORIGINS=https://app.yourdomain.com
   ```
   Restart/redeploy the backend after changing this.
2. **Re-run the same manual test checklist** from the main README's section
   4, but against the live URLs: chat, document upload + grounded question,
   voice (mic permission will now work since you're on HTTPS), history,
   theme toggle.
3. **Watch memory on first request.** The first `/voice` or `/chat`-with-
   DocumentSearch call after a fresh deploy will be a little slower while
   models finish initializing (less so if you're using the Dockerfile's
   build-time pre-download step — see below).
4. **Rotate your API keys** if they were ever pasted into a chat, ticket, or
   committed to git by mistake — treat `GROQ_API_KEY` and `TAVILY_API_KEY`
   as secrets, injected only via your host's environment variable settings,
   never committed to the repo.

---

## 6. A note on what wasn't load-tested

This guide and the accompanying `Dockerfile`s were written carefully and
match how each platform documents its own Docker/volume/env-var support, but
they have **not** been built and run end-to-end in this authoring
environment (which has no Docker and limited disk). Before pointing real
users at a production deployment, do one full dry run — spin up the
cheapest tier on your chosen platform, run the test checklist above against
it, and only then point a real domain and real traffic at it.
