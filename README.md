# CARA — Conversational AI Research Agent

A multilingual AI agent that searches your documents and the live web, then answers in your language out loud.

## What is CARA?

CARA combines three powerful capabilities:

- **RAG** — Upload any PDF and ask questions about it
- **Live web search** — Searches the internet for real-time information  
- **Multilingual voice** — Speak in Telugu, Hindi, Tamil, Malayalam, Kannada or English and hear answers back

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Groq LLaMA-4 Scout (free API) |
| Agent | LangChain tool-calling agent |
| Vector DB | ChromaDB (local) |
| Embeddings | sentence-transformers |
| Web search | Tavily API |
| Voice input | OpenAI Whisper |
| Text to speech | gTTS |
| Translation | deep-translator |
| Frontend | Streamlit |


Prerequisites

Python 3.10 or 3.11
ffmpeg installed and added to PATH
Free API keys from Groq and Tavily
