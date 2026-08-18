#!/usr/bin/env python3
"""
CHAOS TYPE ZERO Scheduler — Hinglish time parsing + full cron support
Supports: cron (all 5 fields), natural language, Hinglish time expressions
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

CTZ_ROOT = Path(__file__).parent.parent
SCHEDULE_DIR = CTZ_ROOT / "data"
CONFIG_FILE = SCHEDULE_DIR / "schedule_config.json"

# === Hinglish Time Parser ===
# Each pattern: regex → lambda that returns timedelta from NOW
HINGLISH_PATTERNS = [
    # Minutes
    (r"agle\s+(\d+)\s*minute",     lambda m: timedelta(minutes=int(m.group(1)))),
    (r"(\d+)\s*minute\s*baad",     lambda m: timedelta(minutes=int(m.group(1)))),
    (r"(\d+)\s*min\s*baad",        lambda m: timedelta(minutes=int(m.group(1)))),
    (r"(\d+)\s*min\b",             lambda m: timedelta(minutes=int(m.group(1)))),
    (r"(\d+)\s*minute",            lambda m: timedelta(minutes=int(m.group(1)))),
    # Hours
    (r"(\d+)\s*ghante?\s*baad",    lambda m: timedelta(hours=int(m.group(1)))),
    (r"(\d+)\s*hour\s*baad",       lambda m: timedelta(hours=int(m.group(1)))),
    (r"(\d+)\s*hours?",            lambda m: timedelta(hours=int(m.group(1)))),
    # Days
    (r"(\d+)\s*din\s*baad",        lambda m: timedelta(days=int(m.group(1)))),
    (r"(\d+)\s*day\s*baad",        lambda m: timedelta(days=int(m.group(1)))),
    (r"(\d+)\s*days?",             lambda m: timedelta(days=int(m.group(1)))),
    # Tomorrow ("kal") with specific time
    (r"kal\s+subah\s+(\d{1,2})",  lambda m: _next_day_at(int(m.group(1)), 0)),   # kal subah 9
    (r"kal\s+dopahar\s+(\d{1,2})", lambda m: _next_day_at(int(m.group(1)), 12)),  # kal dopahar 2
    (r"kal\s+raat\s+(\d{1,2})",   lambda m: _next_day_at(int(m.group(1)), 12)),  # kal raat 10
    (r"kal\s+(\d{1,2})",          lambda m: _next_day_at(int(m.group(1)), 0)),   # kal 10
    # Today ("aaj")
    (r"aaj\s*subah\s*(\d{1,2})",  lambda m: _today_at(int(m.group(1)), 0)),
    (r"aaj\s*raat\s*(\d{1,2})",   lambda m: _today_at(int(m.group(1)), 12)),
    (r"aaj\s*raat",                lambda m: timedelta(hours=max(0, 21 - datetime.now().hour))),
    # Instant
    (r"abhi",                       lambda m: timedelta(seconds=0)),
    (r"turant",                     lambda m: timedelta(seconds=0)),
    (r"jaldi",                      lambda m: timedelta(minutes=5)),
    # Weekly
    (r"hafte?\s*mein",             lambda m: timedelta(weeks=1)),
    (r"weekly",                     lambda m: timedelta(weeks=1)),
    # Daily
    (r"roz",                        lambda m: timedelta(days=1)),
    (r"daily",                      lambda m: timedelta(days=1)),
    (r"har\s*din",                  lambda m: timedelta(days=1)),
]


def _today_at(hour, period_offset=0):
    """Calculate timedelta to a specific hour today.
    
    period_offset: 0 = AM (subah), 12 = PM (raat/dopahar).
    If hour >= 12, offset is ignored (already PM).
    """
    now = datetime.now()
    target_hour = hour + period_offset if hour < 12 else hour
    target = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return target - now


def _next_day_at(hour, period_offset=0):
    """Calculate timedelta to a specific hour tomorrow.
    
    period_offset: 0 = AM (subah), 12 = PM (raat/dopahar).
    """
    now = datetime.now()
    target_hour = hour + period_offset if hour < 12 else hour
    tomorrow = now + timedelta(days=1)
    target = tomorrow.replace(hour=target_hour, minute=0, second=0, microsecond=0)
    return target - now


def parse_hinglish_time(text):
    """Parse Hinglish time expressions into timedelta"""
    text_lower = text.lower()
    for pattern, handler in HINGLISH_PATTERNS:
        match = re.search(pattern, text_lower)
        if match:
            return handler(match)
    return None


# === Full Cron Parser (all 5 fields) ===
DAYS_OF_WEEK = {"sun": 0, "mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6}


def _parse_cron_field(field, min_val, max_val):
    """Parse a single cron field into a set of valid values.
    
    Supports: *, */N, N-M, N,M,O, and plain N.
    """
    values = set()

    for part in field.split(","):
        part = part.strip()

        # Star or star with step: */N
        if part.startswith("*/"):
            step = int(part[2:])
            values.update(range(min_val, max_val + 1, step))
        elif part == "*":
            values.update(range(min_val, max_val + 1))
        # Range: N-M
        elif "-" in part:
            start, end = part.split("-", 1)
            values.update(range(int(start), int(end) + 1))
        # Single value (may be day name like "mon")
        else:
            # Try as number first
            try:
                values.add(int(part))
            except ValueError:
                # Try as day name
                day_num = DAYS_OF_WEEK.get(part.lower())
                if day_num is not None:
                    values.add(day_num)

    return sorted(values)


def parse_cron(expr):
    """Parse full 5-field cron expression into next run time.
    
    Format: minute hour day-of-month month day-of-week
    Examples:
        0 9 * * *       → every day at 9:00
        0 9 * * 1       → every Monday at 9:00
        30 18 1,15 * *  → 1st and 15th of every month at 18:30
        0 */2 * * *     → every 2 hours
    """
    parts = expr.strip().split()
    if len(parts) != 5:
        return None

    minute_f, hour_f, dom_f, month_f, dow_f = parts

    # Parse each field
    valid_minutes = _parse_cron_field(minute_f, 0, 59)
    valid_hours = _parse_cron_field(hour_f, 0, 23)
    valid_dom = _parse_cron_field(dom_f, 1, 31)
    valid_month = _parse_cron_field(month_f, 1, 12)
    valid_dow = _parse_cron_field(dow_f, 0, 6)  # 0=Sun, 6=Sat

    if not valid_minutes or not valid_hours:
        return None

    now = datetime.now()
    next_run = now.replace(second=0, microsecond=0) + timedelta(minutes=1)

    # Search up to 366 days ahead
    for _ in range(366 * 24 * 60):
        # Check month
        if next_run.month not in valid_month:
            next_run = (next_run.replace(day=1, hour=0, minute=0) + timedelta(days=32)).replace(day=1)
            continue

        # Check day of month
        if next_run.day not in valid_dom:
            next_run = (next_run + timedelta(days=1)).replace(hour=0, minute=0)
            continue

        # Check day of week (Python: Monday=0, Sunday=6; cron: Sunday=0, Monday=1)
        cron_dow = (next_run.weekday() + 1) % 7
        if cron_dow not in valid_dow:
            next_run = (next_run + timedelta(days=1)).replace(hour=0, minute=0)
            continue

        # Check hour
        if next_run.hour not in valid_hours:
            next_run = (next_run + timedelta(hours=1)).replace(minute=0)
            continue

        # Check minute
        if next_run.minute not in valid_minutes:
            next_run += timedelta(minutes=1)
            continue

        return next_run

    return None  # No valid run found in 366 days


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
                        # For cron tasks, calculate next run
                        if task.get("cron"):
                            next_run = parse_cron(task["cron"])
                            if next_run:
                                task["parsed_schedule"] = next_run.isoformat()
                except (ValueError, TypeError):
                    pass
        return due

    def mark_run(self, name):
        """Mark a task as run and update counters."""
        for task in self.tasks.get("tasks", []):
            if task["name"] == name:
                task["last_run"] = datetime.now().isoformat()
                task["run_count"] = task.get("run_count", 0) + 1
                self._save_config()
                return task
        return None


if __name__ == "__main__":
    scheduler = ChaosScheduler()

    # Test Hinglish parsing
    tests = [
        "5 minute baad",
        "2 ghante baad",
        "3 din baad",
        "abhi",
        "kal 10",
        "kal subah 9",
        "kal raat 10",
        "aaj raat 11",
        "roz",
        "daily",
    ]

    print("=== Hinglish Time Parsing ===")
    for test in tests:
        delta = parse_hinglish_time(test)
        if delta:
            target = datetime.now() + delta
            print(f"  '{test}' → {target.strftime('%Y-%m-%d %H:%M')}")
        else:
            print(f"  '{test}' → no match")

    print("\n=== Cron Parsing ===")
    cron_tests = [
        "0 9 * * *",        # daily 9am
        "0 9 * * 1",        # every Monday 9am
        "30 18 * * 5",      # every Friday 6:30pm
        "0 */2 * * *",      # every 2 hours
        "5 4 * * 0",        # every Sunday 4:05am
    ]
    for expr in cron_tests:
        next_run = parse_cron(expr)
        if next_run:
            print(f"  '{expr}' → {next_run.strftime('%Y-%m-%d %H:%M')}")
        else:
            print(f"  '{expr}' → parse error")
