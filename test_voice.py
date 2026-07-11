# test_voice.py
from voice import text_to_speech, translate_from_english
import os
import time

test_sentence = "Hello, I am CARA, your AI research agent. I can help you find answers."

languages = {
    "en": "English",
    "te": "Telugu",
    "hi": "Hindi",
    "ta": "Tamil",
    "ml": "Malayalam",
    "kn": "Kannada",
}

for code, name in languages.items():
    print(f"\nTesting {name}...")
    if code != "en":
        translated = translate_from_english(test_sentence, code)
        print(f"{name}: {translated}")
    else:
        translated = test_sentence

    path = text_to_speech(translated, lang=code)
    print(f"Audio saved: {path}")
    os.startfile(path)
    time.sleep(8)  