# app.py — CARA FINAL | Centered layout, proper buttons, working nav
import streamlit as st
import tempfile, os, warnings, base64, hashlib
warnings.filterwarnings("ignore")

os.environ["PATH"] += os.pathsep + r"C:\Users\Lavanya\Downloads\ffmpeg-master-latest-win64-gpl-shared\ffmpeg-master-latest-win64-gpl-shared\bin"

from agent import run_agent
from rag_engine import load_pdf, chunk_text, create_vector_store
from voice import text_to_speech, translate_from_english, transcribe_audio, translate_to_english

st.set_page_config(
    page_title="CARA — AI Research Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DEFAULTS = {
    "logged_in": False, "username": "",
    "messages": [], "lang": "en",
    "doc_chunks": 0, "doc_files": 0,
    "page": "splash", "theme": "dark",
    "last_audio_hash": "", "docs_indexed": False,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

LANGS = {"en":"English","te":"తెలుగు","hi":"हिंदी","ta":"தமிழ்","ml":"മലയാളം","kn":"ಕನ್ನಡ"}
dark = st.session_state.theme == "dark"

BG     = "#07040f" if dark else "#f4f2ff"
BG2    = "#100c1e" if dark else "#ffffff"
BG3    = "#1a1530" if dark else "#ececf9"
CARD   = "#1c1736" if dark else "#ffffff"
BORDER = "#2e2655" if dark else "#d4cff0"
TEXT   = "#f0eeff" if dark else "#150f30"
TEXT2  = "#9d8ec8" if dark else "#6655aa"
TEXT3  = "#5a4e80" if dark else "#9988bb"
PURPLE = "#7c3aed"
ACC    = "#a855f7"
GRAD   = "linear-gradient(135deg,#7c3aed,#9333ea,#c026d3)"

def img_b64(path):
    for p in [path, os.path.join(os.path.dirname(os.path.abspath(__file__)), path)]:
        try:
            with open(p,"rb") as f: return base64.b64encode(f.read()).decode()
        except: pass
    return None

ROBOT_SVG = """<svg viewBox="0 0 200 220" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:100%;">
  <defs>
    <linearGradient id="rg1" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:#7c3aed"/><stop offset="100%" style="stop-color:#c026d3"/></linearGradient>
    <linearGradient id="rg2" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:#6d28d9"/><stop offset="100%" style="stop-color:#9333ea"/></linearGradient>
    <filter id="glow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <line x1="100" y1="18" x2="100" y2="40" stroke="#a855f7" stroke-width="3" stroke-linecap="round"/>
  <circle cx="100" cy="12" r="7" fill="url(#rg1)" filter="url(#glow)"/>
  <rect x="55" y="40" width="90" height="70" rx="20" fill="url(#rg2)" filter="url(#glow)"/>
  <circle cx="82" cy="68" r="12" fill="#1a0a3a"/><circle cx="118" cy="68" r="12" fill="#1a0a3a"/>
  <circle cx="82" cy="68" r="7" fill="url(#rg1)"/><circle cx="118" cy="68" r="7" fill="url(#rg1)"/>
  <circle cx="84" cy="66" r="3" fill="white" opacity="0.9"/><circle cx="120" cy="66" r="3" fill="white" opacity="0.9"/>
  <path d="M 82 85 Q 100 98 118 85" stroke="#a855f7" stroke-width="3" fill="none" stroke-linecap="round"/>
  <rect x="90" y="110" width="20" height="12" rx="4" fill="#5b21b6"/>
  <rect x="45" y="122" width="110" height="75" rx="20" fill="url(#rg2)" filter="url(#glow)"/>
  <rect x="70" y="138" width="60" height="40" rx="10" fill="#1a0a3a" opacity="0.5"/>
  <circle cx="85" cy="153" r="6" fill="url(#rg1)"/><circle cx="100" cy="153" r="6" fill="#22c55e"/><circle cx="115" cy="153" r="6" fill="#f59e0b"/>
  <rect x="78" y="165" width="44" height="5" rx="3" fill="#a855f7" opacity="0.6"/>
  <rect x="15" y="128" width="28" height="55" rx="14" fill="url(#rg2)"/>
  <rect x="157" y="128" width="28" height="55" rx="14" fill="url(#rg2)"/>
  <circle cx="29" cy="188" r="10" fill="url(#rg1)"/><circle cx="171" cy="188" r="10" fill="url(#rg1)"/>
  <rect x="68" y="197" width="26" height="20" rx="8" fill="#5b21b6"/>
  <rect x="106" y="197" width="26" height="20" rx="8" fill="#5b21b6"/>
</svg>"""

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
html,body,.stApp{{background:{BG}!important;font-family:'Inter',sans-serif;color:{TEXT};}}
#MainMenu,footer,header,.stDeployButton,[data-testid="stToolbar"]{{display:none!important;}}
.block-container{{padding:0!important;max-width:100%!important;}}
section[data-testid="stSidebar"]{{display:none!important;}}
::-webkit-scrollbar{{width:4px;}}.stScrollbar{{display:none;}}
::-webkit-scrollbar-thumb{{background:{BORDER};border-radius:4px;}}

/* ── centered wrapper for auth pages ── */
.auth-wrap{{
  min-height:100vh;
  display:flex;align-items:center;justify-content:center;
  padding:2rem 1rem;
  background:radial-gradient(ellipse at 50% 0%,rgba(124,58,237,0.2) 0%,{BG} 65%);
}}
.auth-card{{
  width:100%;max-width:420px;
  background:{CARD};
  border:1px solid {BORDER};
  border-radius:24px;
  padding:2.5rem 2rem;
  box-shadow:0 24px 80px rgba(0,0,0,0.4);
  margin:0 auto;
}}
.auth-logo{{
  width:60px;height:60px;border-radius:18px;
  background:{GRAD};
  display:flex;align-items:center;justify-content:center;
  font-size:28px;margin:0 auto 1.5rem;
  box-shadow:0 8px 24px rgba(124,58,237,0.5);
}}
.auth-h{{
  font-family:'Space Grotesk',sans-serif;
  font-size:1.5rem;font-weight:700;
  color:{TEXT};text-align:center;margin-bottom:0.4rem;
}}
.auth-sub{{font-size:13px;color:{TEXT2};text-align:center;margin-bottom:1.75rem;}}

/* social buttons */
.soc-btn{{
  display:flex;align-items:center;justify-content:center;gap:10px;
  width:100%;padding:11px 16px;border-radius:12px;
  font-size:13px;font-weight:500;cursor:pointer;
  margin-bottom:10px;
  border:1px solid {BORDER};
  background:{BG3};color:{TEXT};
  transition:background 0.15s;
  text-decoration:none;
}}
.soc-btn:hover{{background:{BORDER};}}
.divider{{
  display:flex;align-items:center;gap:10px;margin:1.25rem 0;
}}
.div-line{{flex:1;height:1px;background:{BORDER};}}
.div-txt{{font-size:12px;color:{TEXT3};white-space:nowrap;}}
.field-lbl{{
  font-size:11px;font-weight:600;color:{TEXT2};
  text-transform:uppercase;letter-spacing:0.07em;
  margin-bottom:6px;
}}

/* ── SPLASH ── */
.splash-wrap{{
  min-height:100vh;
  background:radial-gradient(ellipse at 50% 0%,rgba(124,58,237,0.25) 0%,{BG} 60%);
  display:flex;flex-direction:column;
  align-items:center;justify-content:center;
  text-align:center;padding:3rem 2rem;
  position:relative;overflow:hidden;
}}
.splash-glow{{
  position:absolute;top:0;left:50%;transform:translateX(-50%);
  width:600px;height:300px;
  background:radial-gradient(ellipse,rgba(124,58,237,0.2) 0%,transparent 70%);
  pointer-events:none;
}}
.robot-anim{{
  width:clamp(180px,25vw,260px);
  animation:float 3s ease-in-out infinite;
  margin-bottom:2rem;
  filter:drop-shadow(0 0 40px rgba(168,85,247,0.5));
  position:relative;z-index:2;
}}
@keyframes float{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-16px)}}}}
.splash-badge{{
  display:inline-flex;align-items:center;gap:6px;
  background:rgba(124,58,237,0.15);
  border:1px solid rgba(124,58,237,0.35);
  border-radius:100px;padding:6px 18px;
  font-size:12px;color:{ACC};letter-spacing:0.05em;
  margin-bottom:2rem;position:relative;z-index:2;
}}
.splash-h{{
  font-family:'Space Grotesk',sans-serif;
  font-size:clamp(1.8rem,4vw,2.5rem);font-weight:700;
  color:{TEXT};margin-bottom:0.75rem;
  position:relative;z-index:2;
}}
.splash-p{{
  font-size:15px;color:{TEXT2};line-height:1.65;
  max-width:360px;margin:0 auto 2.5rem;
  position:relative;z-index:2;
}}

/* ── TOP NAV (main app) ── */
.topnav{{
  background:{BG2};border-bottom:1px solid {BORDER};
  position:sticky;top:0;z-index:500;width:100%;
}}
.topnav-inner{{
  max-width:1200px;margin:0 auto;
  display:flex;align-items:center;
  justify-content:space-between;
  padding:0 2rem;height:60px;gap:1rem;
}}
.nav-brand{{
  font-family:'Space Grotesk',sans-serif;
  font-size:1.2rem;font-weight:700;color:{TEXT};
  display:flex;align-items:center;gap:8px;flex-shrink:0;
}}
.brand-dot{{
  width:9px;height:9px;border-radius:50%;
  background:{ACC};box-shadow:0 0 8px {ACC};
  animation:pulse-dot 2s infinite;
}}
@keyframes pulse-dot{{0%,100%{{opacity:1}}50%{{opacity:0.5}}}}

/* nav pill group */
.nav-pills{{
  display:flex;align-items:center;gap:2px;
  background:{BG3};border:1px solid {BORDER};
  border-radius:100px;padding:3px;
}}
/* individual pill — styled via Streamlit button */
.nav-right-items{{display:flex;align-items:center;gap:8px;flex-shrink:0;}}
.badge-online{{
  display:flex;align-items:center;gap:5px;
  background:rgba(34,197,94,0.1);
  border:1px solid rgba(34,197,94,0.25);
  border-radius:100px;padding:4px 12px;
  font-size:11px;color:#22c55e;
}}
.dot-green{{width:5px;height:5px;border-radius:50%;background:#22c55e;animation:pulse-dot 2s infinite;}}
.user-chip{{
  display:flex;align-items:center;gap:7px;
  background:{BG3};border:1px solid {BORDER};
  border-radius:100px;padding:4px 14px 4px 4px;
  font-size:13px;color:{TEXT};
}}
.uav{{
  width:26px;height:26px;border-radius:50%;
  background:{GRAD};
  display:flex;align-items:center;justify-content:center;
  font-size:11px;font-weight:700;color:#fff;
}}

/* ── PAGE CONTENT ── */
.pg{{max-width:1200px;margin:0 auto;padding:2rem 2rem 3rem;}}
.pg-narrow{{max-width:700px;}}
.pg-h{{
  font-family:'Space Grotesk',sans-serif;
  font-size:clamp(1.2rem,2.5vw,1.5rem);
  font-weight:700;color:{TEXT};margin-bottom:1rem;
}}

/* ── HERO ── */
.hero-wrap{{
  padding:5rem 2rem 4rem;
  border-bottom:1px solid {BORDER};
  max-width:1200px;margin:0 auto;
}}
.hero-grid{{
  display:grid;grid-template-columns:1fr 1fr;
  gap:4rem;align-items:center;
}}
.hero-eye{{
  display:inline-flex;align-items:center;gap:6px;
  background:rgba(124,58,237,0.1);
  border:1px solid rgba(124,58,237,0.3);
  border-radius:100px;padding:5px 16px;
  font-size:12px;color:{ACC};letter-spacing:0.06em;
  text-transform:uppercase;margin-bottom:1.5rem;
}}
.hero-h{{
  font-family:'Space Grotesk',sans-serif;
  font-size:clamp(2rem,4vw,3.5rem);
  font-weight:700;color:{TEXT};
  line-height:1.1;letter-spacing:-0.03em;
  margin-bottom:1.2rem;
}}
.hero-h em{{
  font-style:italic;
  background:{GRAD};
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
}}
.hero-p{{font-size:16px;color:{TEXT2};line-height:1.7;margin-bottom:2rem;font-weight:300;}}
.hero-langs{{display:flex;gap:8px;flex-wrap:wrap;}}
.hl{{
  padding:5px 14px;border-radius:100px;font-size:12px;
  border:1px solid {BORDER};color:{TEXT2};background:{BG3};
}}
.hero-robot{{
  width:100%;max-width:320px;margin:0 auto;display:block;
  animation:float 3s ease-in-out infinite;
  filter:drop-shadow(0 0 40px rgba(168,85,247,0.45));
}}

/* ── CHAT ── */
.chat-shell{{
  background:{CARD};border:1px solid {BORDER};
  border-radius:16px;overflow:hidden;margin-bottom:1rem;
}}
.chat-head{{
  padding:0.9rem 1.25rem;border-bottom:1px solid {BORDER};
  display:flex;align-items:center;justify-content:space-between;
}}
.chat-head-t{{font-size:14px;font-weight:600;color:{TEXT};}}
.chat-head-s{{font-size:11px;color:{TEXT3};}}
.chat-scroll{{
  min-height:340px;max-height:460px;
  overflow-y:auto;padding:1.25rem;
  display:flex;flex-direction:column;gap:14px;
}}
.cempty{{
  display:flex;flex-direction:column;
  align-items:center;justify-content:center;
  min-height:300px;gap:12px;text-align:center;
}}
.cempty-orb{{
  width:68px;height:68px;border-radius:50%;
  background:{GRAD};
  display:flex;align-items:center;justify-content:center;
  font-size:28px;
  box-shadow:0 8px 32px rgba(124,58,237,0.45);
  animation:float 3s ease-in-out infinite;
}}
.cempty-h{{font-family:'Space Grotesk',sans-serif;font-size:1rem;font-weight:600;color:{TEXT};}}
.cempty-p{{font-size:13px;color:{TEXT3};line-height:1.5;max-width:240px;}}

/* messages */
.mrow{{display:flex;gap:10px;align-items:flex-end;}}
.mrow.u{{flex-direction:row-reverse;}}
.mav{{width:28px;height:28px;border-radius:50%;background:{GRAD};flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:#fff;}}
.mav.u{{background:{BG3};border:1px solid {BORDER};color:{TEXT2};}}
.mbody{{max-width:78%;}}
.mn{{font-size:10px;letter-spacing:0.06em;color:{TEXT3};margin-bottom:4px;}}
.mn.r{{text-align:right;}}
.bc{{background:{BG3};border:1px solid {BORDER};border-radius:4px 16px 16px 16px;padding:0.8rem 1rem;font-size:14px;line-height:1.65;color:{TEXT};}}
.bu{{background:{GRAD};border-radius:16px 4px 16px 16px;padding:0.8rem 1rem;font-size:14px;line-height:1.65;color:#fff;}}

/* ── CARDS ── */
.card{{background:{CARD};border:1px solid {BORDER};border-radius:16px;padding:1.25rem;margin-bottom:1rem;}}
.card-t{{font-size:10px;font-weight:600;color:{TEXT3};text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.9rem;}}
.trow{{display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid {BORDER};font-size:13px;color:{TEXT2};}}
.trow:last-child{{border-bottom:none;}}
.td{{width:7px;height:7px;border-radius:50%;flex-shrink:0;}}
.td1{{background:{ACC};}} .td2{{background:{TEXT3};}} .td3{{background:#d4a847;}}
.bnum{{font-family:'Space Grotesk',sans-serif;font-size:2.8rem;font-weight:700;color:{TEXT};line-height:1;}}
.blbl{{font-size:11px;color:{TEXT3};margin-top:4px;}}
.indexed-pill{{
  display:inline-flex;align-items:center;gap:6px;
  background:rgba(34,197,94,0.1);
  border:1px solid rgba(34,197,94,0.3);
  border-radius:100px;padding:5px 14px;
  font-size:12px;color:#22c55e;margin-bottom:0.75rem;
}}
.inp-shell{{background:{CARD};border:1px solid {BORDER};border-radius:14px;padding:0.75rem 1.1rem 0.5rem;margin-bottom:0.75rem;}}
.inp-hint{{font-size:11px;color:{TEXT3};margin-top:3px;}}
.mic-card{{background:{CARD};border:1px solid {BORDER};border-radius:14px;padding:1rem;text-align:center;margin-bottom:0.75rem;}}
.mic-top{{font-size:11px;color:{TEXT3};letter-spacing:0.06em;text-transform:uppercase;margin-bottom:0.6rem;}}
.mic-bot{{font-size:11px;color:{TEXT3};margin-top:0.6rem;opacity:0.6;}}
.heard{{font-size:12px;color:{ACC};padding:7px 12px;background:rgba(168,85,247,0.1);border-radius:8px;margin-top:8px;border:1px solid rgba(168,85,247,0.3);text-align:left;}}

/* ── voice page ── */
.voice-orb{{
  width:120px;height:120px;border-radius:50%;
  background:{GRAD};margin:0 auto 1.5rem;
  display:flex;align-items:center;justify-content:center;
  font-size:44px;
  box-shadow:0 0 60px rgba(124,58,237,0.5),0 0 120px rgba(124,58,237,0.2);
  animation:float 3s ease-in-out infinite;
}}

/* ── RESPONSIVE ── */
@media(max-width:900px){{
  .hero-grid{{grid-template-columns:1fr;gap:2rem;}}
  .hero-robot{{max-width:220px;}}
}}
@media(max-width:640px){{
  .topnav-inner{{padding:0 1rem;}}
  .pg{{padding:1.25rem 1rem 2rem;}}
  .hero-wrap{{padding:3rem 1rem 2.5rem;}}
}}

/* ══════════════════════════════
   STREAMLIT WIDGET FIXES
══════════════════════════════ */

/* ── nav buttons: pill style, NOT full width ── */
div[data-testid="stHorizontalBlock"] .stButton>button{{
  background:transparent!important;
  color:{TEXT2}!important;
  border:none!important;
  border-radius:100px!important;
  font-size:13px!important;
  font-weight:500!important;
  padding:7px 18px!important;
  width:auto!important;
  box-shadow:none!important;
  transition:all 0.15s!important;
  font-family:'Inter',sans-serif!important;
}}
div[data-testid="stHorizontalBlock"] .stButton>button:hover{{
  background:rgba(255,255,255,0.07)!important;
  color:{TEXT}!important;
  transform:none!important;
}}

/* ── primary action buttons: full width purple ── */
.primary-btn .stButton>button{{
  background:{GRAD}!important;color:#fff!important;
  border:none!important;border-radius:12px!important;
  font-size:14px!important;font-family:'Space Grotesk',sans-serif!important;
  font-weight:600!important;padding:0.75rem 1.5rem!important;
  width:100%!important;letter-spacing:0.02em!important;
  box-shadow:0 4px 20px rgba(124,58,237,0.35)!important;
  transition:all 0.2s!important;
}}
.primary-btn .stButton>button:hover{{
  box-shadow:0 6px 28px rgba(124,58,237,0.55)!important;
  transform:translateY(-1px)!important;
}}

/* ── small sidebar/language buttons ── */
.sm-btn .stButton>button{{
  background:transparent!important;
  color:{TEXT2}!important;
  border:1px solid {BORDER}!important;
  border-radius:8px!important;
  font-size:12px!important;
  font-weight:500!important;
  padding:5px 12px!important;
  width:100%!important;
  box-shadow:none!important;
  transition:all 0.15s!important;
  font-family:'Inter',sans-serif!important;
}}
.sm-btn .stButton>button:hover{{
  background:rgba(124,58,237,0.15)!important;
  color:{ACC}!important;
  border-color:{PURPLE}!important;
  transform:none!important;
}}

/* ── splash/login primary button ── */
.splash-action .stButton>button,
.login-action .stButton>button{{
  background:{GRAD}!important;color:#fff!important;
  border:none!important;border-radius:12px!important;
  font-size:15px!important;font-family:'Space Grotesk',sans-serif!important;
  font-weight:600!important;padding:0.8rem 2rem!important;
  box-shadow:0 4px 20px rgba(124,58,237,0.4)!important;
  transition:all 0.2s!important;
  width:auto!important;
  min-width:200px!important;
}}
.splash-action .stButton>button:hover,
.login-action .stButton>button:hover{{
  box-shadow:0 6px 28px rgba(124,58,237,0.6)!important;
  transform:translateY(-1px)!important;
}}

/* ── text inputs — VISIBLE IN DARK MODE ── */
.stTextInput>div>div>input{{
  background:{BG3}!important;
  border:1.5px solid {BORDER}!important;
  border-radius:12px!important;
  color:{TEXT}!important;
  font-size:14px!important;
  padding:10px 14px!important;
  caret-color:{ACC}!important;
}}
.stTextInput>div>div>input::placeholder{{
  color:{TEXT3}!important;opacity:1!important;
}}
.stTextInput>div>div>input:focus{{
  border-color:{PURPLE}!important;
  box-shadow:0 0 0 2px rgba(124,58,237,0.25)!important;
  outline:none!important;
}}
.stTextInput label{{
  color:{TEXT2}!important;font-size:12px!important;
  font-weight:600!important;letter-spacing:0.05em!important;
  text-transform:uppercase!important;
}}

/* file uploader */
div[data-testid="stFileUploader"] label{{display:none!important;}}
div[data-testid="stFileUploader"]>div{{
  background:{BG3}!important;
  border:1.5px dashed {BORDER}!important;
  border-radius:14px!important;
}}
div[data-testid="stFileUploader"] small{{color:{TEXT3}!important;font-size:12px!important;}}

/* chat input */
div[data-testid="stChatInput"]>div{{
  background:{BG3}!important;border:1px solid {BORDER}!important;
  border-radius:12px!important;box-shadow:none!important;
}}
div[data-testid="stChatInput"] textarea{{
  background:transparent!important;border:none!important;
  color:{TEXT}!important;font-size:14px!important;
  caret-color:{ACC}!important;
}}
div[data-testid="stChatInput"] textarea::placeholder{{color:{TEXT3}!important;opacity:1!important;}}

/* misc */
.stAudio{{border-radius:12px!important;margin-top:6px;}}
.stSpinner>div{{color:{ACC}!important;}}
.stSuccess>div{{background:rgba(34,197,94,0.1)!important;color:#22c55e!important;border-radius:10px!important;border:1px solid rgba(34,197,94,0.3)!important;}}
</style>
""", unsafe_allow_html=True)

# ── helpers ──
def show_messages(uname):
    initial = uname[0].upper() if uname else "U"
    st.markdown('<div class="chat-scroll">', unsafe_allow_html=True)
    if not st.session_state.messages:
        st.markdown(f"""
        <div class="cempty">
          <div class="cempty-orb">🤖</div>
          <div class="cempty-h">Hi {uname}! I'm CARA</div>
          <div class="cempty-p">Ask anything — I search your documents and the live web</div>
        </div>""", unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages[-16:]:
            if msg["role"]=="user":
                st.markdown(f'<div class="mrow u"><div class="mbody"><div class="mn r">YOU</div><div class="bu">{msg["content"]}</div></div><div class="mav u">{initial}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="mrow"><div class="mav">C</div><div class="mbody"><div class="mn">CARA</div><div class="bc">{msg["content"]}</div></div></div>', unsafe_allow_html=True)
                if msg.get("audio"): st.audio(msg["audio"])
    st.markdown('</div>', unsafe_allow_html=True)

def text_input(key="m"):
    st.markdown('<div class="inp-shell">', unsafe_allow_html=True)
    user_in = st.chat_input("Ask anything…", key=f"ci_{key}")
    st.markdown(f'<div class="inp-hint">↵ send · searches docs + web automatically</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    if user_in:
        st.session_state.messages.append({"role":"user","content":user_in,"audio":None})
        with st.spinner("CARA is thinking…"):
            resp = run_agent(user_in)
            lang = st.session_state.lang
            disp = translate_from_english(resp,lang) if lang!="en" else resp
            aud = text_to_speech(disp,lang=lang)
        st.session_state.messages.append({"role":"assistant","content":disp,"audio":aud})
        st.rerun()

def mic_widget(key="m"):
    st.markdown('<div class="mic-card">', unsafe_allow_html=True)
    st.markdown('<div class="mic-top">🎤 click mic · speak · click stop</div>', unsafe_allow_html=True)
    try:
        from audio_recorder_streamlit import audio_recorder
        ab = audio_recorder(text="",recording_color=PURPLE,neutral_color=BORDER,
                           icon_name="microphone",icon_size="2x",
                           pause_threshold=2.0,key=f"ar_{key}")
        if ab and len(ab)>2000:
            h = hashlib.md5(ab).hexdigest()
            if h != st.session_state.last_audio_hash:
                st.session_state.last_audio_hash = h
                with tempfile.NamedTemporaryFile(delete=False,suffix=".wav") as tmp:
                    tmp.write(ab); tp=tmp.name
                with st.spinner("Transcribing…"):
                    r=transcribe_audio(tp); ut=r["text"].strip(); dl=r["language"]
                try: os.unlink(tp)
                except: pass
                if ut:
                    st.markdown(f'<div class="heard">🎤 ({dl}): {ut}</div>', unsafe_allow_html=True)
                    with st.spinner("CARA is thinking…"):
                        eq=translate_to_english(ut,dl)
                        resp=run_agent(eq)
                        reply=translate_from_english(resp,dl) if dl!="en" else resp
                        ap=text_to_speech(reply,lang=dl)
                    st.session_state.messages.append({"role":"user","content":f"🎤 {ut}","audio":None})
                    st.session_state.messages.append({"role":"assistant","content":reply,"audio":ap})
                    st.audio(ap,autoplay=True)
                    st.rerun()
    except ImportError:
        st.warning("pip install audio-recorder-streamlit")
    st.markdown(f'<div class="mic-bot">Telugu · Hindi · Tamil · Malayalam · Kannada · English</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def sidebar_panel(key="r"):
    st.markdown(f'<div class="card"><div class="card-t">Session</div><div class="bnum">{len(st.session_state.messages)//2:02d}</div><div class="blbl">questions answered</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="card"><div class="card-t">Tools</div><div class="trow"><div class="td td1"></div>Document RAG</div><div class="trow"><div class="td td2"></div>Web search</div><div class="trow"><div class="td td3"></div>Calculator</div></div>', unsafe_allow_html=True)
    if st.session_state.docs_indexed:
        st.markdown(f'<div class="indexed-pill">✓ {st.session_state.doc_files} doc · {st.session_state.doc_chunks} chunks</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="card"><div class="card-t">Language</div>', unsafe_allow_html=True)
    for code,label in LANGS.items():
        tick = "✓ " if code==st.session_state.lang else ""
        st.markdown('<div class="sm-btn">', unsafe_allow_html=True)
        if st.button(f"{tick}{label}",key=f"lb_{key}_{code}"):
            st.session_state.lang=code; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="sm-btn">', unsafe_allow_html=True)
    if st.button("↺ Clear chat",key=f"clr_{key}"):
        st.session_state.messages=[]; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════
# ROUTING
# ════════════════════════════════════════════
page = st.session_state.page

# ── SPLASH ──
if page=="splash":
    robot_b64 = img_b64("robot.png")
    robot_html = f'<img src="data:image/png;base64,{robot_b64}" class="robot-anim" style="width:clamp(180px,25vw,260px);"/>' if robot_b64 \
        else f'<div class="robot-anim" style="width:clamp(180px,25vw,260px);">{ROBOT_SVG}</div>'

    st.markdown(f"""
    <div class="splash-wrap">
      <div class="splash-glow"></div>
      <div class="splash-badge">✦ &nbsp;Personal AI Buddy</div>
      {robot_html}
      <h1 class="splash-h">How may I help you today!</h1>
      <p class="splash-p">Your multilingual AI research agent. Search documents, browse the web, and speak in any Indian language.</p>
    </div>
    """, unsafe_allow_html=True)

    c1,c2,c3 = st.columns([1,1,1])
    with c2:
        st.markdown('<div class="splash-action">', unsafe_allow_html=True)
        if st.button("Get Started →", key="splash_go"):
            st.session_state.page="login"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ── LOGIN ──
elif page=="login":
    # Centered card using columns
    col_l, col_c, col_r = st.columns([1,1.2,1])
    with col_c:
        st.markdown(f"""
        <div style="padding:3rem 0;">
          <div class="auth-card">
            <div class="auth-logo">🤖</div>
            <h2 class="auth-h">Welcome to CARA</h2>
            <p class="auth-sub">Sign in to your personal AI research agent</p>
            <div class="soc-btn">
              <svg width="16" height="16" viewBox="0 0 18 18">
                <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908C16.658 14.215 17.64 11.907 17.64 9.2z" fill="#4285F4"/>
                <path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332C2.438 15.983 5.482 18 9 18z" fill="#34A853"/>
                <path d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z" fill="#FBBC05"/>
                <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0 5.482 0 2.438 2.017.957 4.958L3.964 6.29C4.672 4.163 6.656 3.58 9 3.58z" fill="#EA4335"/>
              </svg>
              &nbsp;Continue with Google
            </div>
            <div class="soc-btn">✉️ &nbsp;Continue with Email</div>
            <div class="divider">
              <div class="div-line"></div>
              <div class="div-txt">or sign in with name</div>
              <div class="div-line"></div>
            </div>
            <div class="field-lbl">Your name</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        username = st.text_input("","", placeholder="Enter your name",
                                  label_visibility="collapsed", key="uname_field")
        st.markdown('<div style="height:0.75rem;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="login-action">', unsafe_allow_html=True)
        if st.button("Sign In →", key="login_go"):
            if username.strip():
                st.session_state.logged_in = True
                st.session_state.username = username.strip()
                st.session_state.page = "home"
                st.rerun()
            else:
                st.error("Please enter your name.")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="text-align:center;margin-top:1rem;font-size:12px;color:{TEXT3};">No account needed · Just enter your name</div>', unsafe_allow_html=True)

# ── MAIN APP ──
elif st.session_state.logged_in:
    uname = st.session_state.username
    initial = uname[0].upper() if uname else "U"
    page = st.session_state.page

    # ── TOP NAV ──
    pages = [("home","Home"),("chat","Chat"),("docs","Documents"),("voice","Voice"),("settings","Settings")]
    active_name = dict(pages).get(page,"Home")
    st.markdown(f"""
    <div class="topnav">
      <div class="topnav-inner">
        <div class="nav-brand"><div class="brand-dot"></div>CARA</div>
        <div class="nav-pills" id="nav-pills-display">
          {"".join([f'<span style="padding:7px 18px;border-radius:100px;font-size:13px;font-weight:{"600" if page==p else "400"};color:{""+TEXT+"" if page==p else TEXT2};background:{""+BG2+"" if page==p else "transparent"};cursor:pointer;">{n}</span>' for p,n in pages])}
        </div>
        <div class="nav-right-items">
          <div class="badge-online"><div class="dot-green"></div>Online</div>
          <div class="user-chip"><div class="uav">{initial}</div>{uname}</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── functional nav buttons ──
    nav_cols = st.columns(len(pages)+1)
    for i,(p,n) in enumerate(pages):
        with nav_cols[i]:
            if st.button(n, key=f"nav_{p}"):
                st.session_state.page=p; st.rerun()
    with nav_cols[-1]:
        theme_lbl = "☀️" if dark else "🌙"
        if st.button(theme_lbl, key="nav_theme"):
            st.session_state.theme = "dark" if dark else "light"; st.rerun()

    # ════ HOME ════
    if page=="home":
        robot_b64 = img_b64("robot.png")
        hero_img = f'<img src="data:image/png;base64,{robot_b64}" class="hero-robot"/>' if robot_b64 \
            else f'<div class="hero-robot" style="max-width:280px;">{ROBOT_SVG}</div>'

        lang_pills = "".join([f'<span class="hl">{l}</span>' for l in LANGS.values()])
        st.markdown(f"""
        <div class="hero-wrap">
          <div class="hero-grid">
            <div>
              <div class="hero-eye">◎ &nbsp; RAG · Agent · Voice · Multilingual</div>
              <h1 class="hero-h">Research <em>everything.</em></h1>
              <p class="hero-p">Speak or type in any Indian language. CARA searches your documents and the live web, then answers out loud.</p>
              <div class="hero-langs">{lang_pills}</div>
            </div>
            <div style="display:flex;justify-content:center;">{hero_img}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="pg">', unsafe_allow_html=True)
        st.markdown(f'<div class="pg-h">Quick start</div>', unsafe_allow_html=True)
        left, right = st.columns([2.5,1], gap="large")
        with left:
            st.markdown('<div class="chat-shell"><div class="chat-head"><div class="chat-head-t">CARA</div><div class="chat-head-s">AI Research Agent</div></div>', unsafe_allow_html=True)
            show_messages(uname)
            st.markdown('</div>', unsafe_allow_html=True)
            text_input("home")
            mic_widget("home")
        with right:
            sidebar_panel("home")
        st.markdown('</div>', unsafe_allow_html=True)

    # ════ CHAT ════
    elif page=="chat":
        st.markdown('<div class="pg">', unsafe_allow_html=True)
        st.markdown(f'<div class="pg-h">AI Chat</div>', unsafe_allow_html=True)
        if st.session_state.docs_indexed:
            st.markdown(f'<div class="indexed-pill">✓ Document loaded · {st.session_state.doc_chunks} chunks · searching automatically</div>', unsafe_allow_html=True)
        left, right = st.columns([2.5,1], gap="large")
        with left:
            st.markdown('<div class="chat-shell"><div class="chat-head"><div class="chat-head-t">Chat with CARA</div></div>', unsafe_allow_html=True)
            show_messages(uname)
            st.markdown('</div>', unsafe_allow_html=True)
            text_input("chat")
            mic_widget("chat")
        with right:
            sidebar_panel("chat")
        st.markdown('</div>', unsafe_allow_html=True)

    # ════ DOCUMENTS ════
    elif page=="docs":
        st.markdown('<div class="pg">', unsafe_allow_html=True)
        st.markdown(f'<div class="pg-h">Your Documents</div>', unsafe_allow_html=True)
        if st.session_state.docs_indexed:
            st.markdown(f'<div class="indexed-pill">✓ {st.session_state.doc_files} file · {st.session_state.doc_chunks} chunks indexed and ready</div>', unsafe_allow_html=True)
        left, right = st.columns([1.6,1], gap="large")
        with left:
            st.markdown('<div class="card"><div class="card-t">Upload PDF</div>', unsafe_allow_html=True)
            st.caption("Notes, textbooks, reports — CARA indexes and remembers everything")
            up = st.file_uploader("",type=["pdf"],accept_multiple_files=True,
                                   label_visibility="collapsed",key="fup")
            if up:
                st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
                if st.button("⚡ Index Documents"):
                    with st.spinner(f"Indexing {len(up)} file(s)…"):
                        chunks=[]
                        for f in up:
                            with tempfile.NamedTemporaryFile(delete=False,suffix=".pdf") as tmp:
                                tmp.write(f.read()); tp=tmp.name
                            chunks.extend(chunk_text(load_pdf(tp)))
                            try: os.unlink(tp)
                            except: pass
                        create_vector_store(chunks)
                        st.session_state.doc_files=len(up)
                        st.session_state.doc_chunks=len(chunks)
                        st.session_state.docs_indexed=True
                    st.success(f"✓ Indexed {len(chunks)} chunks. Now ask questions below!")
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            if st.session_state.docs_indexed:
                st.markdown(f'<div style="font-family:Space Grotesk,sans-serif;font-size:1rem;font-weight:600;color:{TEXT};margin:1rem 0 0.5rem;">Ask about your document</div>', unsafe_allow_html=True)
                st.markdown('<div class="chat-shell"><div class="chat-head"><div class="chat-head-t">Document Q&A</div></div>', unsafe_allow_html=True)
                show_messages(uname)
                st.markdown('</div>', unsafe_allow_html=True)
                text_input("docs")
                mic_widget("docs")
        with right:
            st.markdown(f'<div class="card"><div class="card-t">Index Status</div><div class="bnum">{st.session_state.doc_chunks:03d}</div><div class="blbl">chunks · {st.session_state.doc_files} file(s)</div></div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="card">
              <div class="card-t">How RAG works</div>
              <div style="font-size:13px;color:{TEXT2};line-height:2.1;">
                1. Upload your PDF<br>
                2. Split into 500-char chunks<br>
                3. Embed each chunk as vector<br>
                4. Store in ChromaDB locally<br>
                5. Match to your question<br>
                6. LLM answers with context
              </div>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ════ VOICE ════
    elif page=="voice":
        st.markdown('<div class="pg">', unsafe_allow_html=True)
        left, right = st.columns([1.6,1], gap="large")
        with left:
            st.markdown(f"""
            <div style="text-align:center;padding:2rem 0 1rem;">
              <div class="voice-orb">🎤</div>
              <div style="font-family:Space Grotesk,sans-serif;font-size:1.4rem;font-weight:700;color:{TEXT};margin-bottom:0.5rem;">Speak to CARA</div>
              <div style="font-size:14px;color:{TEXT2};line-height:1.6;margin-bottom:1.5rem;">Click mic · Speak slowly · Click stop<br>CARA auto-detects your language</div>
              <div style="display:flex;gap:8px;flex-wrap:wrap;justify-content:center;">
                {"".join([f'<span class="hl">{l}</span>' for l in LANGS.values()])}
              </div>
            </div>""", unsafe_allow_html=True)
            mic_widget("voice_pg")
            if st.session_state.messages:
                last_a = [m for m in st.session_state.messages if m["role"]=="assistant"]
                if last_a:
                    st.markdown(f'<div class="card"><div class="card-t">Last answer</div><div style="font-size:14px;color:{TEXT};line-height:1.65;">{last_a[-1]["content"][:400]}</div></div>', unsafe_allow_html=True)
        with right:
            st.markdown(f'<div class="card"><div class="card-t">Response Language</div>', unsafe_allow_html=True)
            for code,label in LANGS.items():
                tick="✓ " if code==st.session_state.lang else ""
                st.markdown('<div class="sm-btn">', unsafe_allow_html=True)
                if st.button(f"{tick}{label}",key=f"vl_{code}"):
                    st.session_state.lang=code; st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="card">
              <div class="card-t">Tips for accuracy</div>
              <div style="font-size:13px;color:{TEXT2};line-height:2.1;">
                • One sentence at a time<br>
                • Pause before stopping<br>
                • Avoid background noise<br>
                • Short questions work best<br>
                • Telugu: pronounce clearly
              </div>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ════ SETTINGS ════
    elif page=="settings":
        st.markdown(f'<div class="pg" style="max-width:680px;">', unsafe_allow_html=True)
        st.markdown(f'<div class="pg-h">Settings</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="card"><div class="card-t">Profile</div><div style="display:flex;align-items:center;gap:12px;"><div class="uav" style="width:44px;height:44px;border-radius:50%;background:{GRAD};display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:700;color:#fff;">{initial}</div><div><div style="font-size:15px;font-weight:600;color:{TEXT};">{uname}</div><div style="font-size:12px;color:{TEXT3};">Signed in</div></div></div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="card"><div class="card-t">Theme</div>', unsafe_allow_html=True)
        st.markdown('<div class="sm-btn">', unsafe_allow_html=True)
        if st.button(f"{'🌙 Switch to Dark' if not dark else '☀️ Switch to Light'}",key="theme_s"):
            st.session_state.theme="dark" if dark else "light"; st.rerun()
        st.markdown('</div></div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="card"><div class="card-t">Tech Stack</div>
          <div class="trow"><div class="td td1"></div>Groq LLaMA-4 Scout — agent brain</div>
          <div class="trow"><div class="td td1"></div>ChromaDB + sentence-transformers — RAG</div>
          <div class="trow"><div class="td td2"></div>Tavily — real-time web search</div>
          <div class="trow"><div class="td td2"></div>OpenAI Whisper — voice transcription</div>
          <div class="trow"><div class="td td3"></div>gTTS + deep-translator — multilingual</div>
        </div>""", unsafe_allow_html=True)
        st.markdown(f'<div class="card"><div class="card-t">Session</div>', unsafe_allow_html=True)
        c1,c2 = st.columns(2)
        with c1:
            st.markdown('<div class="sm-btn">', unsafe_allow_html=True)
            if st.button("↺ Clear chat history",key="clr_s"):
                st.session_state.messages=[]; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="sm-btn">', unsafe_allow_html=True)
            if st.button("🚪 Sign out",key="so_s"):
                for k,v in DEFAULTS.items():
                    st.session_state[k]=v
                st.session_state.page="splash"; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

else:
    st.session_state.page="login"; st.rerun()