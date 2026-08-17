#!/usr/bin/env python3
"""
NEXUS Task Classifier
Auto-classifies user requests into task types for routing
12 task types with confidence scoring
"""

import re
from typing import Tuple

# === Task Type Definitions ===
TASK_TYPES = {
    "code": {
        "keywords": ["code", "function", "class", "debug", "fix bug", "implement", "script", "program", "api", "endpoint", "refactor", "compile", "build", "test", "git", "commit", "push", "pull", "merge"],
        "patterns": [r"write.*code", r"create.*script", r"fix.*bug", r"implement.*function", r"python", r"javascript", r"typescript", r"rust", r"go ", r"java\b"],
        "priority": 1,
    },
    "research": {
        "keywords": ["research", "search", "find", "look up", "google", "what is", "how does", "explain", "tell me about", "information", "docs", "documentation", "wiki"],
        "patterns": [r"what is", r"how to", r"explain", r"tell me", r"research", r"search for", r"look up"],
        "priority": 2,
    },
    "pentest": {
        "keywords": ["scan", "nmap", "vulnerability", "exploit", "pentest", "security", "recon", "attack", "hack", "渗透", "ceh", "nuclei", "nikto", "sqlmap", "hydra", "shodan", "amass", "gobuster"],
        "patterns": [r"scan.*target", r"nmap", r"vulnerability", r"pentest", r"recon.*target", r"security scan", r"hack.*target"],
        "priority": 3,
    },
    "vision": {
        "keywords": ["screenshot", "screen", "image", "picture", "photo", "ocr", "read screen", "what's on screen", "capture"],
        "patterns": [r"screenshot", r"read.*screen", r"what.*on.*screen", r"capture.*screen", r"ocr"],
        "priority": 4,
    },
    "hinglish": {
        "keywords": ["bhai", "yaar", "kya", "hai", "karo", "matlab", "samajh", "bol", "sun", "dekh", "ye woh", "accha", "theek hai", "chalo", "ruk", "ruk ja", "kar de", "ho gaya", "nahi", "haan", "bata"],
        "patterns": [r"bhai", r"yaar", r"kya hai", r"kar de", r"bata", r"samajh", r"matlab"],
        "priority": 5,
    },
    "write": {
        "keywords": ["write", "essay", "article", "blog", "document", "report", "summary", "draft", "content", "copy", "文案"],
        "patterns": [r"write.*essay", r"write.*article", r"write.*blog", r"write.*report", r"draft", r"compose"],
        "priority": 6,
    },
    "ml": {
        "keywords": ["train", "model", "dataset", "machine learning", "deep learning", "neural network", "pytorch", "tensorflow", "fine-tune", "evaluate", "predict", "inference", "pipeline"],
        "patterns": [r"train.*model", r"machine learning", r"deep learning", r"neural", r"pytorch", r"tensorflow", r"fine.?tune"],
        "priority": 7,
    },
    "data": {
        "keywords": ["data", "csv", "json", "database", "query", "sql", "analyze", "statistics", "chart", "graph", "visualization", "pandas", "numpy"],
        "patterns": [r"analyze.*data", r"csv", r"json", r"database", r"sql query", r"chart", r"graph"],
        "priority": 8,
    },
    "voice": {
        "keywords": ["voice", "speak", "listen", "whisper", "transcribe", "audio", "record", "microphone", "speech"],
        "patterns": [r"transcribe", r"whisper", r"voice", r"speak", r"listen", r"record.*audio"],
        "priority": 9,
    },
    "agent": {
        "keywords": ["automate", "schedule", "cron", "workflow", "pipeline", "trigger", "webhook", "bot"],
        "patterns": [r"automate", r"schedule", r"cron", r"workflow", r"pipeline"],
        "priority": 10,
    },
    "speed": {
        "keywords": ["quick", "fast", "urgent", "asap", "jaldi", "turant", "abhi"],
        "patterns": [r"quick", r"fast", r"urgent", r"asap", r"jaldi", r"turant"],
        "priority": 11,
    },
    "general": {
        "keywords": [],
        "patterns": [],
        "priority": 99,
    },
}


def classify_task(user_input: str) -> Tuple[str, float]:
    """
    Classify user input into a task type.

    Returns: (task_type, confidence)
    """
    input_lower = user_input.lower().strip()
    scores = {}

    for task_type, config in TASK_TYPES.items():
        if task_type == "general":
            continue

        score = 0

        # Keyword matching
        for keyword in config["keywords"]:
            if keyword in input_lower:
                score += 2

        # Pattern matching (stronger signal)
        for pattern in config["patterns"]:
            if re.search(pattern, input_lower):
                score += 3

        if score > 0:
            scores[task_type] = score

    if not scores:
        return "general", 0.5

    # Get best match
    best_type = max(scores, key=scores.get)
    max_score = scores[best_type]

    # Calculate confidence (0.0 - 1.0)
    confidence = min(1.0, max_score / 10.0)

    # Handle conflicts: if hinglish + other type, prefer the other
    if best_type == "hinglish" and len(scores) > 1:
        other_types = {k: v for k, v in scores.items() if k != "hinglish"}
        if other_types:
            second_best = max(other_types, key=other_types.get)
            if other_types[second_best] >= scores["hinglish"]:
                return second_best, 0.7

    return best_type, confidence


def get_task_chain(task_type: str) -> dict:
    """Get the recommended provider chain for a task type"""
    from .smart_brain import TASK_CHAINS
    return TASK_CHAINS.get(task_type, TASK_CHAINS["agent"])


if __name__ == "__main__":
    # Test cases
    tests = [
        "bhai ye code fix kar de",
        "scan target 192.168.1.1",
        "write an essay about AI",
        "what is machine learning",
        "screenshot leke bata kya hai",
        "jaldi se ye kar de",
        "train a model on this dataset",
        "research quantum computing",
        "nmap se port scan karo",
        "create a Python script for web scraping",
    ]

    for test in tests:
        task_type, confidence = classify_task(test)
        print(f"  '{test}'")
        print(f"    → {task_type} (confidence: {confidence:.1%})")
        print()
