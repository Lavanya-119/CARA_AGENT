# voice.py — fixed Telugu + all Indian languages
import os
os.environ["PATH"] += os.pathsep + r"C:\Users\Lavanya\Downloads\ffmpeg-master-latest-win64-gpl-shared\ffmpeg-master-latest-win64-gpl-shared\bin"

import whisper
from gtts import gTTS
from deep_translator import GoogleTranslator
import tempfile

print("Loading Whisper model...")
whisper_model = whisper.load_model("base")
print("Whisper ready!")

LANG_MAP = {
    "en": "en", "te": "te", "hi": "hi",
    "ta": "ta", "ml": "ml", "kn": "kn"
}

def transcribe_audio(audio_file_path: str) -> dict:
    result = whisper_model.transcribe(
        audio_file_path,
        language=None,        # auto-detect
        task="transcribe",    # keep original language, don't translate
        fp16=False            # CPU safe
    )
    return {
        "text": result["text"].strip(),
        "language": result["language"]
    }

def translate_to_english(text: str, source_lang: str) -> str:
    if source_lang == "en" or not text.strip():
        return text
    try:
        return GoogleTranslator(source="auto", target="en").translate(text)
    except Exception as e:
        print(f"Translation to English failed: {e}")
        return text

def translate_from_english(text: str, target_lang: str) -> str:
    if target_lang == "en" or not text.strip():
        return text
    try:
        # Split into chunks of 4500 chars to avoid API limit
        chunks = [text[i:i+4500] for i in range(0, len(text), 4500)]
        translated_chunks = []
        for chunk in chunks:
            t = GoogleTranslator(source="en", target=target_lang).translate(chunk)
            translated_chunks.append(t if t else chunk)
        return " ".join(translated_chunks)
    except Exception as e:
        print(f"Translation from English failed: {e}")
        return text  # fallback to English

def text_to_speech(text: str, lang: str = "en") -> str:
    tts_lang = LANG_MAP.get(lang, "en")
    # Limit to 500 chars for speech — full text shown in chat
    speech_text = text[:500]
    try:
        tts = gTTS(text=speech_text, lang=tts_lang, slow=False)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(tmp.name)
        return tmp.name
    except Exception as e:
        print(f"TTS failed for {lang}: {e}")
        # Fallback to English TTS
        tts = gTTS(text=speech_text, lang="en", slow=False)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(tmp.name)
        return tmp.name

def full_voice_pipeline(audio_file: str, agent_func) -> dict:
    transcription = transcribe_audio(audio_file)
    user_text = transcription["text"]
    user_lang = transcription["language"]
    english_question = translate_to_english(user_text, user_lang)
    english_answer = agent_func(english_question)
    final_answer = translate_from_english(english_answer, user_lang)
    audio_path = text_to_speech(final_answer, lang=user_lang)
    return {
        "user_said": user_text,
        "detected_language": user_lang,
        "english_question": english_question,
        "answer": final_answer,
        "audio_path": audio_path
    }