#!/usr/bin/env python3
"""
CHAOS TYPE ZERO Self-Healing Memory
Auto-detect and repair memory corruption, validate integrity, rebuild indexes.

Features:
- Integrity checks on all memory databases
- Auto-repair corrupted entries
- Rebuild indexes
- Deduplication
- Health scoring
- Auto-heal on startup
"""

import json
import os
import sqlite3
from pathlib import Path

CTZ_ROOT = Path(__file__).parent.parent
DATA_DIR = CTZ_ROOT / "data"
MEMORY_DIR = DATA_DIR / "memory"
CONTEXT_DIR = DATA_DIR / "context"
CACHE_DIR = DATA_DIR / "cache"


class MemoryHealer:
    """Self-healing memory system — detects and repairs corruption."""
    
    def __init__(self):
        self.databases = {
            "ledger": MEMORY_DIR / "ctz_ledger.db",
            "context": CONTEXT_DIR / "context_bridge.db",
            "cache": CACHE_DIR / "cache.db",
        }
        self.repairs = []
    
    def check_all(self):
        """Run integrity check on all databases."""
        results = {}
        for name, path in self.databases.items():
            if path.exists():
                results[name] = self._check_db(name, path)
            else:
                results[name] = {"status": "missing", "healthy": False, "message": f"Database not found: {path}"}
        return results
    
    def _check_db(self, name, path):
        """Check single database integrity."""
        try:
            conn = sqlite3.connect(str(path))
            c = conn.cursor()
            
            # PRAGMA integrity_check
            c.execute("PRAGMA integrity_check")
            integrity = c.fetchone()[0]
            
            # Count tables
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in c.fetchall()]
            
            # Count rows per table
            table_counts = {}
            for table in tables:
                try:
                    c.execute(f"SELECT COUNT(*) FROM [{table}]")
                    table_counts[table] = c.fetchone()[0]
                except:
                    table_counts[table] = -1
            
            # Check for duplicates in key tables
            duplicates = self._check_duplicates(c, tables)
            
            # Check for NULL/empty critical fields
            orphans = self._check_orphans(c, tables)
            
            conn.close()
            
            healthy = integrity == "ok" and not duplicates and not orphans
            return {
                "status": "ok" if healthy else "needs_repair",
                "healthy": healthy,
                "integrity": integrity,
                "tables": table_counts,
                "duplicates": duplicates,
                "orphans": orphans,
            }
        except Exception as e:
            return {"status": "error", "healthy": False, "error": str(e)}
    
    def _check_duplicates(self, cursor, tables):
        """Check for duplicate entries."""
        dupes = []
        for table in tables:
            try:
                if table == "key_facts":
                    cursor.execute("SELECT fact, COUNT(*) FROM key_facts WHERE is_active = 1 GROUP BY fact HAVING COUNT(*) > 1")
                    rows = cursor.fetchall()
                    if rows:
                        dupes.append({"table": table, "count": len(rows), "items": [r[0][:50] for r in rows[:5]]})
            except:
                pass
        return dupes
    
    def _check_orphans(self, cursor, tables):
        """Check for orphaned records."""
        orphans = []
        try:
            if "context_entries" in tables and "sessions" in tables:
                cursor.execute("""SELECT COUNT(*) FROM context_entries ce 
                    WHERE NOT EXISTS (SELECT 1 FROM sessions s WHERE s.id = ce.session_id)""")
                count = cursor.fetchone()[0]
                if count > 0:
                    orphans.append({"table": "context_entries", "orphaned": count})
        except:
            pass
        return orphans
    
    def heal_all(self):
        """Run auto-repair on all databases."""
        self.repairs = []
        for name, path in self.databases.items():
            if path.exists():
                self._heal_db(name, path)
        return {"repairs": self.repairs}
    
    def _heal_db(self, name, path):
        """Repair single database."""
        try:
            conn = sqlite3.connect(str(path))
            c = conn.cursor()
            
            # 1. Rebuild indexes
            c.execute("PRAGMA optimize")
            self.repairs.append(f"{name}: optimized")
            
            # 2. VACUUM to reclaim space
            c.execute("VACUUM")
            self.repairs.append(f"{name}: vacuumed")
            
            # 3. Deduplicate key_facts
            if name == "context":
                c.execute("""DELETE FROM key_facts WHERE rowid NOT IN (
                    SELECT MIN(rowid) FROM key_facts WHERE is_active = 1 GROUP BY fact
                )""")
                if c.rowcount > 0:
                    self.repairs.append(f"context: removed {c.rowcount} duplicate facts")
                
                # 4. Clean orphaned context entries
                c.execute("""DELETE FROM context_entries WHERE session_id NOT IN (
                    SELECT id FROM sessions
                )""")
                if c.rowcount > 0:
                    self.repairs.append(f"context: removed {c.rowcount} orphaned entries")
            
            # 5. Clean expired cache
            if name == "cache":
                c.execute("DELETE FROM cache_entries WHERE expires_at < CURRENT_TIMESTAMP")
                if c.rowcount > 0:
                    self.repairs.append(f"cache: removed {c.rowcount} expired entries")
            
            # 6. Clean old conversation snapshots
            if name == "context":
                c.execute("DELETE FROM conversation_snapshots WHERE created_at < datetime('now', '-7 days')")
                if c.rowcount > 0:
                    self.repairs.append(f"context: removed {c.rowcount} old snapshots")
            
            conn.commit()
            conn.close()
        except Exception as e:
            self.repairs.append(f"{name}: error - {e}")
    
    def health_score(self):
        """Get overall memory health score (0-100)."""
        results = self.check_all()
        scores = []
        for name, info in results.items():
            if info.get("healthy"):
                scores.append(100)
            elif info.get("status") == "missing":
                scores.append(50)
            else:
                scores.append(30)
        avg = sum(scores) / len(scores) if scores else 0
        return {
            "score": round(avg),
            "databases": {k: v.get("status") for k, v in results.items()},
            "recommendation": "All healthy" if avg >= 90 else "Run heal_all()" if avg >= 50 else "Critical repair needed"
        }
    
    def auto_heal(self):
        """Check health and auto-heal if needed."""
        health = self.health_score()
        if health["score"] < 90:
            repairs = self.heal_all()
            return {"action": "healed", "before_score": health["score"], "repairs": repairs}
        return {"action": "none", "score": health["score"], "message": "All healthy"}


_healer = None

def get_healer():
    global _healer
    if _healer is None:
        _healer = MemoryHealer()
    return _healer


if __name__ == "__main__":
    h = get_healer()
    print("Health:", json.dumps(h.health_score(), indent=2))
    print("Heal:", json.dumps(h.auto_heal(), indent=2))
