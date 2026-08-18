#!/usr/bin/env python3
"""
CHAOS TYPE ZERO Voice Module — Speech-to-Text + Text-to-Speech
Uses: Whisper (local), pyttsx3 (offline TTS)
"""

import os
import sys
import json
import tempfile
import threading
from pathlib import Path

CTZ_ROOT = Path(__file__).parent.parent


class CTZVoice:
    """CHAOS TYPE ZERO Voice Engine — hear and speak"""

    def __init__(self):
        self._stt_model = None
        self._tts_engine = None
        self._tts_lock = threading.Lock()
        self._lang = "en"

    # === Speech-to-Text (Whisper) ===

    def _load_stt(self):
        if self._stt_model is None:
            try:
                import whisper
                self._stt_model = whisper.load_model("base")
            except ImportError:
                return None
        return self._stt_model

    def transcribe_file(self, audio_path: str, language: str = None) -> dict:
        """Transcribe an audio file to text"""
        model = self._load_stt()
        if model is None:
            return {"error": "Whisper not installed. Run: pip install openai-whisper"}

        lang = language or self._lang
        result = model.transcribe(audio_path, language=lang)
        return {
            "text": result["text"].strip(),
            "language": result.get("language", lang),
            "segments": len(result.get("segments", [])),
        }

    def transcribe_bytes(self, audio_bytes: bytes, format: str = "wav",
                         language: str = None) -> dict:
        """Transcribe raw audio bytes"""
        with tempfile.NamedTemporaryFile(suffix=f".{format}", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name
        try:
            return self.transcribe_file(tmp_path, language)
        finally:
            os.unlink(tmp_path)

    # === Text-to-Speech (pyttsx3) ===

    def _load_tts(self):
        if self._tts_engine is None:
            try:
                import pyttsx3
                self._tts_engine = pyttsx3.init()
                self._tts_engine.setProperty("rate", 175)
                self._tts_engine.setProperty("volume", 0.9)
            except Exception:
                return None
        return self._tts_engine

    def speak(self, text: str, rate: int = 175, volume: float = 0.9) -> dict:
        """Speak text aloud"""
        with self._tts_lock:
            engine = self._load_tts()
            if engine is None:
                return {"error": "pyttsx3 not installed. Run: pip install pyttsx3"}
            try:
                engine.setProperty("rate", rate)
                engine.setProperty("volume", volume)
                engine.say(text)
                engine.runAndWait()
                return {"status": "spoken", "text": text[:100] + "..." if len(text) > 100 else text}
            except Exception as e:
                return {"error": str(e)}

    def save_to_file(self, text: str, output_path: str, rate: int = 175) -> dict:
        """Save speech to audio file"""
        with self._tts_lock:
            engine = self._load_tts()
            if engine is None:
                return {"error": "pyttsx3 not installed"}
            try:
                engine.setProperty("rate", rate)
                engine.save_to_file(text, output_path)
                engine.runAndWait()
                return {"status": "saved", "path": output_path}
            except Exception as e:
                return {"error": str(e)}

    def set_voice(self, voice_index: int = None, language: str = "en") -> dict:
        """Set voice (male/female)"""
        engine = self._load_tts()
        if engine is None:
            return {"error": "pyttsx3 not installed"}
        voices = engine.getProperty("voices")
        if voice_index is not None and 0 <= voice_index < len(voices):
            engine.setProperty("voice", voices[voice_index].id)
            return {"status": "set", "voice": voices[voice_index].name}
        return {"voices": [{"id": i, "name": v.name} for i, v in enumerate(voices)]}

    # === Convenience ===

    def listen(self, duration: int = 5) -> dict:
        """Record from mic and transcribe (requires pyaudio)"""
        try:
            import pyaudio
            import wave
        except ImportError:
            return {"error": "pyaudio not installed. Run: pip install pyaudio"}

        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        RECORD_SECONDS = duration

        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                        input=True, frames_per_buffer=CHUNK)

        frames = []
        for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        p.terminate()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wf = wave.open(f.name, "wb")
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b"".join(frames))
            wf.close()
            tmp_path = f.name

        try:
            return self.transcribe_file(tmp_path)
        finally:
            os.unlink(tmp_path)

    def get_status(self) -> dict:
        """Get voice module status"""
        return {
            "stt": "whisper" if self._stt_model else "not loaded",
            "tts": "pyttsx3" if self._tts_engine else "not loaded",
            "language": self._lang,
        }


# Singleton
_voice = None


def get_voice() -> CTZVoice:
    global _voice
    if _voice is None:
        _voice = CTZVoice()
    return _voice


if __name__ == "__main__":
    voice = get_voice()
    print("=== CHAOS TYPE ZERO Voice Module ===")
    print(f"Status: {json.dumps(voice.get_status(), indent=2)}")
    print("\nTesting TTS...")
    result = voice.speak("CHAOS TYPE ZERO voice module initialized. Ready to serve.")
    print(f"TTS: {result}")
