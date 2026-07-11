What is CARA?

CARA is a Conversational AI Research Agent — a production-grade AI application that combines:


RAG (Retrieval Augmented Generation) — upload any PDF and ask questions about it
Real-time web search — searches the live internet for current information
Multilingual voice I/O — speak in Telugu, Hindi, Tamil, Malayalam, Kannada, or English and hear answers back in the same language
Autonomous agent reasoning — decides which tool to use (document search, web search, or calculator) without being told



Unlike a simple chatbot, CARA is an autonomous agent — it plans, executes multi-step tasks, and combines multiple sources to give the best answer.



Demo

Feature Description
🎤 Voice Input       Speak in any Indian language, CARA auto-detects and responds
📄 Document Q&A      Upload a PDF, ask questions, get accurate answers from the content
🌐 Live Web Search   Asks about today's news? CARA searches the internet in real-time
🌍 6 Languages       Telugu · Hindi · Tamil · Malayalam · Kannada · English
🌙 Dark/Light theme  Toggle between themes
🔐 Login system      Personal session for each user


Tech Stack

Layer           Technology
LLM             Groq LLaMA-4 Scout (free API, 1M tokens/day)
Agent framework LangChain tool-calling agent
Vector database ChromaDB (local, no cloud needed)
Embeddings      sentence-transformers all-MiniLM-L6-v2
Web search      Tavily API (free tier, 1000 searches/month)
Voice input     OpenAI Whisper (runs locally, offline)
Text to speech  gTTS (Google Text-to-Speech)
Translation     deep-translator (GoogleTranslator)

Project Structure

cara-agent/
├── app.py                  ← Streamlit dashboard (main UI)
├── agent.py                ← LangChain agent with 3 tools
├── rag_engine.py           ← RAG: PDF loading, chunking, ChromaDB
├── voice.py                ← Whisper + translation + gTTS
├── requirements.txt        ← All Python dependencies
├── .env                    ← API keys (never committed)
├── .gitignore              ← Excludes .env, chroma_db, venv
├── robot.png               ← UI robot image
└── chroma_db/              ← Auto-created, stores embeddings


Getting Started

Prerequisites


Python 3.10 or 3.11
ffmpeg installed and added to PATH
Free API keys from Groq and Tavily