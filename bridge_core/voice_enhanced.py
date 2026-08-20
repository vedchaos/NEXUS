#!/usr/bin/env python3
"""
CHAOS TYPE ZERO Enhanced Voice — Wake word detection and streaming
No heavy voice deps — lightweight keyword/command matching
"""

import re
import json
import hashlib
import sqlite3
import threading
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

CTZ_ROOT = Path(__file__).parent.parent
DATA_DIR = CTZ_ROOT / "data" / "voice_enhanced"

# ── Wake words ──────────────────────────────────────────────────────────

_DEFAULT_WAKE_WORDS = [
    "hey chaos", "ok chaos", "hello chaos", "computer", "assistant",
    "hey nexus", "ok nexus", "nexus", "chaos", "system",
]

# ── Command patterns ────────────────────────────────────────────────────

_COMMAND_PATTERNS = [
    (r'(?:search|find|look\s*(?:up|for))\s+(.+)', "search", ["query"]),
    (r'(?:open|launch|start|run)\s+(.+)', "open", ["target"]),
    (r'(?:close|stop|quit|exit|kill)\s+(.+)', "close", ["target"]),
    (r'(?:create|make|new|add)\s+(.+)', "create", ["target"]),
    (r'(?:delete|remove|destroy|drop)\s+(.+)', "delete", ["target"]),
    (r'(?:set|change|update|modify)\s+(\w+)\s+(?:to|=)\s+(.+)', "set", ["key", "value"]),
    (r'(?:show|display|list|print)\s+(.+)', "show", ["target"]),
    (r'(?:send|email|message)\s+(.+)', "send", ["target"]),
    (r'(?:play|pause|stop)\s+(.+)', "media", ["target"]),
    (r'(?:remind|alert|notify)\s+(?:me\s+(?:to\s+)?)?(.+)', "remind", ["task"]),
    (r'(?:what|how|when|where|who|why|which)\s+(.+)', "query", ["question"]),
    (r'(?:schedule|plan|book)\s+(.+)', "schedule", ["target"]),
    (r'(?:calculate|compute|math)\s+(.+)', "calculate", ["expression"]),
    (r'(?:translate)\s+(.+)\s+(?:to|into)\s+(\w+)', "translate", ["text", "language"]),
    (r'(?:call|dial|phone)\s+(.+)', "call", ["contact"]),
]

# ── Language detection ──────────────────────────────────────────────────

_LANG_INDICATORS = {
    "en": {
        "words": {"the", "is", "are", "was", "were", "have", "has", "can", "will",
                  "this", "that", "with", "for", "not", "you", "all", "but"},
    },
    "es": {
        "words": {"el", "la", "los", "las", "es", "son", "está", "tiene", "como",
                  "pero", "más", "por", "con", "del", "una", "esto", "eso"},
    },
    "fr": {
        "words": {"le", "la", "les", "est", "sont", "avec", "pour", "dans",
                  "mais", "plus", "qui", "que", "pas", "nous", "vous", "être"},
    },
    "de": {
        "words": {"der", "die", "das", "ist", "sind", "mit", "für", "auf",
                  "aber", "auch", "noch", "nicht", "kann", "wird", "haben"},
    },
    "it": {
        "words": {"il", "la", "le", "è", "sono", "con", "per", "non",
                  "che", "questo", "questa", "più", "anche", "hanno", "come"},
    },
    "pt": {
        "words": {"o", "a", "os", "as", "é", "são", "com", "para",
                  "não", "mas", "mais", "tem", "como", "isso", "está"},
    },
    "ja": {"chars": range(0x3040, 0x309F + 1)},
    "ko": {"chars": range(0xAC00, 0xD7AF + 1)},
    "zh": {"chars": range(0x4E00, 0x9FFF + 1)},
    "ar": {"chars": range(0x0600, 0x06FF + 1)},
    "ru": {"chars": range(0x0400, 0x04FF + 1)},
}

# ── Entity extraction ───────────────────────────────────────────────────

_ENTITY_PATTERNS = {
    "email": r'\b[\w.+-]+@[\w-]+\.[\w.]+\b',
    "url": r'https?://\S+',
    "phone": r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
    "date": r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
    "time": r'\b\d{1,2}:\d{2}(?:\s?[ap]m)?\b',
    "number": r'\b\d+(?:\.\d+)?\b',
}


class CTZVoiceEnhanced:
    """CHAOS TYPE ZERO Enhanced Voice — wake word, commands, streaming"""

    def __init__(self, wake_words=None):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._wake_words = wake_words or list(_DEFAULT_WAKE_WORDS)
        self._profiles = {}
        self._history = []
        self._listening = False
        self._db_path = str(DATA_DIR / "voice_enhanced.db")
        self._lock = threading.Lock()
        self._init_db()
        self._load_profiles()

    def _init_db(self):
        conn = sqlite3.connect(self._db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                name TEXT PRIMARY KEY,
                data TEXT,
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS command_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT,
                intent TEXT,
                entities TEXT,
                created_at TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _load_profiles(self):
        try:
            conn = sqlite3.connect(self._db_path)
            for row in conn.execute("SELECT name, data FROM profiles"):
                self._profiles[row[0]] = json.loads(row[1])
            conn.close()
        except Exception:
            pass

    # ── Wake Word Detection ─────────────────────────────────────────────

    def detect_wake_word(self, audio_text):
        text_lower = audio_text.lower().strip()
        for wake in self._wake_words:
            if wake.lower() in text_lower:
                return True
        words = text_lower.split()
        wake_variants = [w.lower() for w in self._wake_words]
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}"
            if bigram in wake_variants:
                return True
        return False

    def add_wake_word(self, word):
        if word.lower() not in [w.lower() for w in self._wake_words]:
            self._wake_words.append(word)

    def remove_wake_word(self, word):
        self._wake_words = [w for w in self._wake_words if w.lower() != word.lower()]

    # ── Command Parsing ─────────────────────────────────────────────────

    def parse_command(self, text):
        text_clean = text.strip()
        intent = "unknown"
        entities = {}
        confidence = 0.0

        for pattern, cmd, params in _COMMAND_PATTERNS:
            match = re.search(pattern, text_clean, re.IGNORECASE)
            if match:
                intent = cmd
                groups = match.groups()
                for i, param in enumerate(params):
                    if i < len(groups):
                        entities[param] = groups[i].strip()
                confidence = 0.85
                break

        for ent_type, ent_pattern in _ENTITY_PATTERNS.items():
            found = re.findall(ent_pattern, text_clean)
            if found:
                entities[ent_type] = found if len(found) > 1 else found[0]

        if intent == "unknown":
            if text_clean.lower().split():
                intent = "freeform"
                entities["raw_text"] = text_clean
                confidence = 0.4

        result = {
            "intent": intent,
            "entities": entities,
            "confidence": confidence,
            "original": text_clean,
            "timestamp": datetime.now().isoformat(),
        }

        with self._lock:
            self._history.append(result)
            if len(self._history) > 200:
                self._history = self._history[-200:]

        try:
            conn = sqlite3.connect(self._db_path)
            conn.execute(
                "INSERT INTO command_history (text, intent, entities, created_at) VALUES (?, ?, ?, ?)",
                (text_clean, intent, json.dumps(entities), datetime.now().isoformat()),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

        return result

    # ── Language Detection ───────────────────────────────────────────────

    def detect_language(self, text):
        for char in text:
            code = ord(char)
            for lang, spec in _LANG_INDICATORS.items():
                if "chars" in spec and code in spec["chars"]:
                    return lang

        words = set(text.lower().split())
        scores = {}
        for lang, spec in _LANG_INDICATORS.items():
            if "words" in spec:
                overlap = len(words & spec["words"])
                scores[lang] = overlap

        if scores:
            best = max(scores, key=scores.get)
            if scores[best] > 0:
                return best

        return "en"

    # ── Voice Profiles ──────────────────────────────────────────────────

    def save_profile(self, name, voice_data):
        profile = {
            "name": name,
            "data": voice_data,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        self._profiles[name] = profile

        try:
            conn = sqlite3.connect(self._db_path)
            conn.execute(
                "INSERT OR REPLACE INTO profiles (name, data, created_at) VALUES (?, ?, ?)",
                (name, json.dumps(profile), profile["created_at"]),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

        return {"status": "saved", "name": name}

    def load_profile(self, name):
        if name in self._profiles:
            return self._profiles[name]
        return {"error": f"Profile '{name}' not found"}

    def list_profiles(self):
        return [
            {"name": k, "created": v.get("created_at")}
            for k, v in self._profiles.items()
        ]

    def delete_profile(self, name):
        if name not in self._profiles:
            return {"error": f"Profile '{name}' not found"}
        del self._profiles[name]
        try:
            conn = sqlite3.connect(self._db_path)
            conn.execute("DELETE FROM profiles WHERE name = ?", (name,))
            conn.commit()
            conn.close()
        except Exception:
            pass
        return {"status": "deleted", "name": name}

    # ── Command History ─────────────────────────────────────────────────

    def get_command_history(self, limit=20):
        results = list(reversed(self._history[-limit:]))
        if len(results) < limit:
            try:
                conn = sqlite3.connect(self._db_path)
                needed = limit - len(results)
                rows = conn.execute(
                    "SELECT text, intent, entities, created_at FROM command_history "
                    "ORDER BY id DESC LIMIT ?",
                    (needed,),
                ).fetchall()
                conn.close()
                for row in reversed(rows):
                    results.append({
                        "intent": row[1],
                        "entities": json.loads(row[2]) if row[2] else {},
                        "original": row[0],
                        "timestamp": row[3],
                    })
            except Exception:
                pass
        return results

    def clear_history(self):
        self._history.clear()
        try:
            conn = sqlite3.connect(self._db_path)
            conn.execute("DELETE FROM command_history")
            conn.commit()
            conn.close()
        except Exception:
            pass

    # ── Continuous Listening ─────────────────────────────────────────────

    def continuous_listen(self, callback=None, interval=0.1):
        self._listening = True

        def _listen_loop():
            import time
            while self._listening:
                time.sleep(interval)

        if callback:
            t = threading.Thread(target=_listen_loop, daemon=True)
            t.start()
            return {"status": "started", "callback": str(callback)}
        return {"status": "started_simulated"}

    def stop_listening(self):
        self._listening = False
        return {"status": "stopped"}

    def is_listening(self):
        return self._listening

    # ── Streaming Simulation ────────────────────────────────────────────

    def simulate_stream(self, text, chunk_size=5):
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append({
                "text": chunk,
                "index": i // chunk_size,
                "is_final": i + chunk_size >= len(words),
            })
        return chunks

    # ── Utilities ───────────────────────────────────────────────────────

    def get_status(self):
        return {
            "module": "CTZVoiceEnhanced",
            "wake_words": len(self._wake_words),
            "profiles": len(self._profiles),
            "history_size": len(self._history),
            "listening": self._listening,
            "features": [
                "detect_wake_word", "parse_command", "detect_language",
                "save_profile", "load_profile", "get_command_history",
                "continuous_listen", "simulate_stream",
            ],
        }


# Singleton
_voice_enhanced = None


def get_voice_enhanced():
    global _voice_enhanced
    if _voice_enhanced is None:
        _voice_enhanced = CTZVoiceEnhanced()
    return _voice_enhanced


if __name__ == "__main__":
    v = get_voice_enhanced()
    print("=== CHAOS TYPE ZERO Enhanced Voice ===")
    print(f"Status: {json.dumps(v.get_status(), indent=2)}")

    print("\n--- Wake Word Detection ---")
    tests = [
        "Hey Chaos, what time is it",
        "Hello there",
        "OK Chaos search for files",
        "Computer open terminal",
    ]
    for t in tests:
        print(f"  '{t}' => {v.detect_wake_word(t)}")

    print("\n--- Command Parsing ---")
    commands = [
        "search for python tutorials",
        "open my email",
        "set volume to 50",
        "what is the weather tomorrow",
        "remind me to buy groceries",
    ]
    for cmd in commands:
        result = v.parse_command(cmd)
        print(f"  '{cmd}' => intent={result['intent']}, entities={result['entities']}")

    print("\n--- Language Detection ---")
    samples = [
        "Hello how are you today",
        "Bonjour comment allez vous",
        "Hola como estas",
    ]
    for s in samples:
        print(f"  '{s}' => {v.detect_language(s)}")

    print("\n--- Streaming Simulation ---")
    stream = v.simulate_stream("The quick brown fox jumps over the lazy dog in the park", chunk_size=4)
    for chunk in stream:
        final = " [FINAL]" if chunk["is_final"] else ""
        print(f"  chunk {chunk['index']}: '{chunk['text']}'{final}")

    print("\n--- Profile Management ---")
    print(v.save_profile("test_user", {"pitch": "medium", "speed": "normal"}))
    print(v.load_profile("test_user"))
    print(v.list_profiles())

    print(f"\n--- Command History ({len(v.get_command_history(10))} entries) ---")
    for h in v.get_command_history(5):
        print(f"  {h['intent']}: {h['original'][:60]}")
