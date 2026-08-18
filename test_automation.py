#!/usr/bin/env python3
"""CHAOS TYPE ZERO Automation Engine — Full Test"""
import json
import time
import sys
from pathlib import Path

CTZ_ROOT = Path(__file__).parent
sys.path.insert(0, str(CTZ_ROOT))

print("=" * 60)
print("  CHAOS TYPE ZERO Automation Engine — Test")
print("=" * 60)

# 1. Import & init
print("\n[1/6] Import & Init...")
from bridge_core.automation import (
    get_engine, ACTION_TYPES, AutoScheduler,
    FileWatcher, URLWatcher, _parse_cron_next, _cron_matches,
)
engine = get_engine()
print(f"  Action types: {list(ACTION_TYPES.keys())}")
print(f"  DB path: {engine.db._path}")

# 2. CRUD
print("\n[2/6] CRUD Operations...")
auto1 = engine.create(
    name="Test Interval",
    trigger_type="interval",
    trigger_config={"seconds": 300},
    actions=[
        {"type": "shell", "params": {"command": "echo hello from CHAOS TYPE ZERO"}},
        {"type": "log", "params": {"message": "Test automation ran"}},
    ],
    description="Test interval automation",
)
print(f"  Created: {auto1['id']} — {auto1['name']}")
assert engine.get(auto1["id"]) is not None
print("  GET: OK")

auto2 = engine.create(
    name="Test Cron",
    trigger_type="cron",
    trigger_config={"expression": "0 22 * * *"},
    actions=[
        {"type": "notify", "params": {"title": "Test", "message": "Cron fired"}},
    ],
)
print(f"  Created: {auto2['id']} — {auto2['name']}")

all_autos = engine.list_all()
print(f"  List: {len(all_autos)} automations")
assert len(all_autos) >= 2

# 3. Enable / Disable
print("\n[3/6] Enable / Disable...")
engine.disable(auto1["id"])
d = engine.get(auto1["id"])
assert not d["enabled"], "Should be disabled"
print("  Disable: OK")

engine.enable(auto1["id"])
e = engine.get(auto1["id"])
assert e["enabled"], "Should be enabled"
print("  Enable: OK")

# 4. Run Now
print("\n[4/6] Run Now (manual trigger)...")
result = engine.run_now(auto1["id"])
print(f"  Status: {result['status']}")
print(f"  Actions run: {result['actions_run']}")
for r in result.get("results", []):
    print(f"    {r['action']}: {r['result'].get('status', r['result'].get('error', 'ok'))}")
assert result["status"] == "success"
print("  Run: OK")

# 5. Presets
print("\n[5/6] Presets...")
auto_backup = engine.preset_auto_backup(str(CTZ_ROOT), interval_hours=1)
print(f"  Auto Backup: {auto_backup['id']} — {auto_backup['name']}")

auto_cleanup = engine.preset_file_cleanup(str(CTZ_ROOT / "data"), max_age_days=7)
print(f"  File Cleanup: {auto_cleanup['id']} — {auto_cleanup['name']}")

auto_report = engine.preset_daily_report()
print(f"  Daily Report: {auto_report['id']} — {auto_report['name']}")

auto_health = engine.preset_health_check(interval_minutes=5)
print(f"  Health Check: {auto_health['id']} — {auto_health['name']}")

# 6. History & Stats
print("\n[6/6] History & Stats...")
history = engine.db.get_history(limit=10)
print(f"  History entries: {len(history)}")

stats = engine.db.stats()
print(f"  Stats: {json.dumps(stats, indent=2)}")

# 7. Cron parser
print("\n  Cron parser test:")
assert _cron_matches(["0", "22", "*", "*", "*"],
                      __import__("datetime").datetime(2026, 1, 1, 22, 0))
print("    0 22 * * * at 22:00: MATCH")
assert not _cron_matches(["0", "22", "*", "*", "*"],
                          __import__("datetime").datetime(2026, 1, 1, 21, 0))
print("    0 22 * * * at 21:00: NO MATCH")
assert _cron_matches(["*/5", "*", "*", "*", "*"],
                      __import__("datetime").datetime(2026, 1, 1, 14, 15))
print("    */5 * * * * at :15: MATCH")
assert _cron_matches(["0", "9", "*", "*", "1-5"],
                      __import__("datetime").datetime(2026, 1, 5, 9, 0))  # Monday
print("    0 9 * * 1-5 on Monday 09:00: MATCH")

# 8. File watcher
print("\n  File watcher test:")
fw = FileWatcher()
r1 = fw.snapshot("test_watch", str(CTZ_ROOT), "*.py")
print(f"    Initial: {r1.get('status')} — {r1.get('files', 0)} files")
assert r1.get("status") == "initial_snapshot"
r2 = fw.snapshot("test_watch", str(CTZ_ROOT), "*.py")
print(f"    Second: changes={r2.get('has_changes', False)}")
assert not r2.get("has_changes", True), "Should be no changes"

# 9. Cleanup
print("\n  Cleanup test automations...")
for a in [auto1, auto2, auto_backup, auto_cleanup, auto_report, auto_health]:
    engine.delete(a["id"])
final = engine.list_all()
print(f"  Remaining: {len(final)} automations")

print("\n" + "=" * 60)
print("  ALL TESTS PASSED!")
print("=" * 60)
