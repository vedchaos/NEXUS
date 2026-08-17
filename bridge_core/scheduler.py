#!/usr/bin/env python3
"""
NEXUS Scheduler — Hinglish time parsing + APScheduler
Supports: cron, natural language, Hinglish time expressions
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

NEXUS_ROOT = Path(__file__).parent.parent
SCHEDULE_DIR = NEXUS_ROOT / "data"
CONFIG_FILE = SCHEDULE_DIR / "schedule_config.json"

# === Hinglish Time Parser ===
HINGLISH_PATTERNS = {
    # Minutes
    r"agle\s+(\d+)\s*minute": lambda m: timedelta(minutes=int(m.group(1))),
    r"(\d+)\s*minute\s*baad": lambda m: timedelta(minutes=int(m.group(1))),
    r"(\d+)\s*min\s*baad": lambda m: timedelta(minutes=int(m.group(1))),
    r"(\d+)\s*min\b": lambda m: timedelta(minutes=int(m.group(1))),
    r"(\d+)\s*minute": lambda m: timedelta(minutes=int(m.group(1))),
    # Hours
    r"(\d+)\s*ghante?\s*baad": lambda m: timedelta(hours=int(m.group(1))),
    r"(\d+)\s*hour\s*baad": lambda m: timedelta(hours=int(m.group(1))),
    r"(\d+)\s*hours?": lambda m: timedelta(hours=int(m.group(1))),
    # Days
    r"(\d+)\s*din\s*baad": lambda m: timedelta(days=int(m.group(1))),
    r"(\d+)\s*day\s*baad": lambda m: timedelta(days=int(m.group(1))),
    r"(\d+)\s*days?": lambda m: timedelta(days=int(m.group(1))),
    # Specific times
    r"kal\s+\w*\s*(\d{1,2})": lambda m: timedelta(days=1),  # kal subah 9 AM, kal raat 10
    r"kal\s+(\d{1,2})": lambda m: timedelta(days=1),  # kal 10 baje
    r"aaj\s*raat\s*(\d{1,2})": lambda m: timedelta(hours=max(0, int(m.group(1)) - datetime.now().hour)),
    r"aaj\s*raat": lambda m: timedelta(hours=12),
    r"abhi": lambda m: timedelta(seconds=0),
    r"turant": lambda m: timedelta(seconds=0),
    r"jaldi": lambda m: timedelta(minutes=5),
    # Weekly
    r"hafte?\s*mein": lambda m: timedelta(weeks=1),
    r"weekly": lambda m: timedelta(weeks=1),
    # Daily
    r"roz": lambda m: timedelta(days=1),
    r"daily": lambda m: timedelta(days=1),
    r"har\s*din": lambda m: timedelta(days=1),
}


def parse_hinglish_time(text):
    """Parse Hinglish time expressions into timedelta"""
    text_lower = text.lower()
    for pattern, handler in HINGLISH_PATTERNS.items():
        match = re.search(pattern, text_lower)
        if match:
            return handler(match)
    return None


def parse_cron(expr):
    """Parse cron expression into next run time"""
    parts = expr.split()
    if len(parts) != 5:
        return None

    now = datetime.now()
    minute, hour, day, month, dow = parts

    next_run = now.replace(second=0, microsecond=0)

    # Simple cron parsing (minute and hour)
    if minute != "*":
        next_run = next_run.replace(minute=int(minute))
    if hour != "*":
        next_run = next_run.replace(hour=int(hour))

    if next_run <= now:
        next_run += timedelta(days=1)

    return next_run


class ChaosScheduler:
    """Task scheduler with Hinglish support"""

    def __init__(self):
        self.tasks = self._load_config()

    def _load_config(self):
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text())
        return {"tasks": []}

    def _save_config(self):
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(self.tasks, indent=2))

    def add_task(self, name, command, schedule, task_type="command"):
        """Add a scheduled task"""
        # Parse schedule
        parsed_schedule = None
        cron_expr = None

        # Try Hinglish first
        delta = parse_hinglish_time(schedule)
        if delta:
            parsed_schedule = (datetime.now() + delta).isoformat()
        # Try cron
        elif re.match(r"^\S+\s+\S+\s+\S+\s+\S+\s+\S+$", schedule):
            cron_expr = schedule
            next_run = parse_cron(schedule)
            if next_run:
                parsed_schedule = next_run.isoformat()

        task = {
            "name": name,
            "command": command,
            "schedule": schedule,
            "parsed_schedule": parsed_schedule,
            "cron": cron_expr,
            "type": task_type,
            "enabled": True,
            "created": datetime.now().isoformat(),
            "last_run": None,
            "run_count": 0,
        }

        self.tasks["tasks"].append(task)
        self._save_config()
        return task

    def list_tasks(self):
        return self.tasks.get("tasks", [])

    def remove_task(self, name):
        self.tasks["tasks"] = [t for t in self.tasks["tasks"] if t["name"] != name]
        self._save_config()

    def get_due_tasks(self):
        """Get tasks that are due to run"""
        now = datetime.now()
        due = []
        for task in self.tasks.get("tasks", []):
            if not task.get("enabled"):
                continue
            if task.get("parsed_schedule"):
                try:
                    schedule_time = datetime.fromisoformat(task["parsed_schedule"])
                    if schedule_time <= now:
                        due.append(task)
                except:
                    pass
        return due


if __name__ == "__main__":
    scheduler = ChaosScheduler()

    # Test Hinglish parsing
    tests = [
        "5 minute baad",
        "2 ghante baad",
        "3 din baad",
        "abhi",
        "kal 10",
        "roz",
        "daily",
    ]

    for test in tests:
        delta = parse_hinglish_time(test)
        if delta:
            target = datetime.now() + delta
            print(f"  '{test}' → {target.strftime('%Y-%m-%d %H:%M')}")
        else:
            print(f"  '{test}' → no match")
