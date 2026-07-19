"""
voice.py — speech-to-text, translation, and text-to-speech pipeline for CARA.

Pipeline for POST /voice:
  1. Transcribe the uploaded audio with Groq's hosted Whisper
     (whisper-large-v3 by default), auto-detecting the spoken language.
  2. If the detected language isn't English, translate the transcript to English.
  3. Run the text agent on the English question.
  4. Translate the answer back to the detected language.
  5. Synthesize speech for that answer with gTTS.
  6. Return everything, including base64-encoded MP3 audio, as JSON.

Why Groq-hosted Whisper instead of the local `openai-whisper` package:
  local `small` is noticeably weaker on lower-resource languages like
  Telugu, Kannada, and Malayalam than it is on English — it will often
  mis-transcribe entire phrases, which then poisons every step downstream
  (bad translation, bad agent input, bad answer). Groq hosts
  `whisper-large-v3` (and a faster `-turbo` variant), which is meaningfully
  more accurate on these languages and requires no local model download at
  all.

Notes:
- gTTS language codes mostly match Whisper/ISO-639-1 codes we care about here
  (en, hi, te, ta, kn, ml), but we fall back to English speech if gTTS
  doesn't support a detected code.
"""

import base64
import logging
import os
import re
import tempfile

from deep_translator import GoogleTranslator
from gtts import gTTS

from agent import get_groq_client, run_agent

logger = logging.getLogger("cara.voice")

# whisper-large-v3-turbo is faster and cheaper; whisper-large-v3 is a touch
# more accurate on harder/lower-resource languages. Override via .env if
# you want to try the turbo variant.
GROQ_WHISPER_MODEL = os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3")

# Languages gTTS is known to support well for this app's target audience.
# If Whisper detects something outside this set, we still answer in English
# and speak the response in English rather than failing outright.
SUPPORTED_TTS_LANGUAGES = {"en", "hi", "te", "ta", "kn", "ml"}

# Groq's hosted Whisper (OpenAI-compatible API) returns the detected language
# as a full word (e.g. "telugu"), not a short ISO-639-1 code (e.g. "te") like
# the local `openai-whisper` package used to. Everything downstream — gTTS,
# deep-translator, the SUPPORTED_TTS_LANGUAGES check — expects the short
# code, so we normalize here. This map covers the languages this app
# explicitly supports; anything else is passed through lowercased as a
# best-effort guess.
LANGUAGE_NAME_TO_CODE = {
    "english": "en",
    "telugu": "te",
    "hindi": "hi",
    "tamil": "ta",
    "kannada": "kn",
    "malayalam": "ml",
}


def _normalize_language(raw_language: str) -> str:
    normalized = (raw_language or "en").strip().lower()
    return LANGUAGE_NAME_TO_CODE.get(normalized, normalized)


def transcribe_audio(file_path: str) -> tuple[str, str]:
    """
    Transcribe an audio file using Groq's hosted Whisper, auto-detecting the
    spoken language. Returns (transcript, detected_language_code) where the
    language code is normalized to a short ISO-639-1-style code (e.g. "te"),
    regardless of whether the API returned a full word or a code.
    """
    client = get_groq_client()

    with open(file_path, "rb") as f:
        response = client.audio.transcriptions.create(
            file=(os.path.basename(file_path), f.read()),
            model=GROQ_WHISPER_MODEL,
            response_format="verbose_json",
            # No `language=` param passed on purpose - omitting it lets
            # Whisper auto-detect rather than forcing a language, since we
            # support multiple.
        )

    transcript = (getattr(response, "text", "") or "").strip()
    raw_language = getattr(response, "language", None) or "en"
    detected_language = _normalize_language(raw_language)

    logger.info(
        "Groq Whisper transcription: raw_lang=%r, normalized_lang=%s, transcript=%r",
        raw_language,
        detected_language,
        transcript,
    )
    return transcript, detected_language


def translate_to_english(text: str, source_language: str) -> str:
    if not text.strip() or source_language == "en":
        return text
    try:
        result = GoogleTranslator(source=source_language, target="en").translate(text)
        logger.info("Translated to English: %r -> %r", text, result)
        return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("Translation to English failed (%s); using original text.", exc)
        return text


def translate_from_english(text: str, target_language: str) -> str:
    if not text.strip() or target_language == "en":
        return text
    try:
        result = GoogleTranslator(source="en", target=target_language).translate(text)
        logger.info("Translated from English: %r -> %r", text, result)
        return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("Translation from English failed (%s); using English text.", exc)
        return text


def clean_text_for_speech(text: str) -> str:
    """
    Strip Markdown table/formatting artifacts before handing text to gTTS.
    This is a backstop — the system prompt already asks the model to avoid
    Markdown — but if a table slips through anyway, this keeps gTTS from
    reading pipe characters and separator dashes out loud ("dash dash dash").
    """
    cleaned = text

    # Drop table separator rows entirely, e.g. "|------|------|" or "---|---"
    cleaned = re.sub(r"^\s*[|\-:\s]+\s*$", "", cleaned, flags=re.MULTILINE)

    # Table rows: turn "| A | B | C |" into "A, B, C"
    def _row_to_prose(match: "re.Match[str]") -> str:
        cells = [c.strip() for c in match.group(0).split("|") if c.strip()]
        return ", ".join(cells) + ". "

    cleaned = re.sub(r"^\s*\|.*\|\s*$", _row_to_prose, cleaned, flags=re.MULTILINE)

    # Remove any remaining stray pipes.
    cleaned = cleaned.replace("|", " ")

    # Strip bold/italic markers and heading hashes, keep the underlying text.
    cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"\*(.*?)\*", r"\1", cleaned)
    cleaned = re.sub(r"^\s*#{1,6}\s*", "", cleaned, flags=re.MULTILINE)

    # Strip leading bullet markers ("- " or "* ") from list items.
    cleaned = re.sub(r"^\s*[-*]\s+", "", cleaned, flags=re.MULTILINE)

    # Collapse leftover runs of dashes/whitespace from stripped separators.
    cleaned = re.sub(r"-{2,}", " ", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{2,}", " ", cleaned)

    return cleaned.strip()


def synthesize_speech(text: str, language: str) -> str:
    """
    Generate speech audio for the given text and return it as a base64 string
    (raw MP3 bytes, no data: URI prefix — the frontend builds that itself).
    """
    tts_language = language if language in SUPPORTED_TTS_LANGUAGES else "en"
    speakable_text = clean_text_for_speech(text)

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        tts = gTTS(text=speakable_text, lang=tts_language)
        tts.save(tmp_path)
        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()
        return base64.b64encode(audio_bytes).decode("utf-8")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def process_voice_query(audio_path: str) -> dict:
    """
    Run the full voice pipeline described in the module docstring and return
    a dict matching the /voice response contract.
    """
    user_said, detected_language = transcribe_audio(audio_path)

    if not user_said:
        raise ValueError(
            "Could not transcribe any speech from the recording. "
            "Please try recording again with a clearer, longer clip (2-3s minimum)."
        )

    english_question = translate_to_english(user_said, detected_language)
    english_answer = run_agent(english_question)
    localized_answer = translate_from_english(english_answer, detected_language)
    audio_base64 = synthesize_speech(localized_answer, detected_language)

    return {
        "user_said": user_said,
        "detected_language": detected_language,
        "english_question": english_question,
        "answer": localized_answer,
        "audio_base64": audio_base64,
    }
