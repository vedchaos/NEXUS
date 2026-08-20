#!/usr/bin/env python3
"""
CHAOS TYPE ZERO Cache — LLM Response Caching
Cache LLM responses to save money and improve speed.

Features:
- Hash-based cache keys (prompt + model + provider)
- TTL-based expiration
- Hit/miss statistics
- SQLite persistence
- Auto-cleanup of old entries
"""

import hashlib
import json
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path

CTZ_ROOT = Path(__file__).parent.parent
DATA_DIR = CTZ_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
DB_PATH = CACHE_DIR / "cache.db"

CACHE_DIR.mkdir(parents=True, exist_ok=True)


class Cache:
    """LLM response cache with TTL and statistics."""
    
    def __init__(self, db_path=None, default_ttl_hours=24):
        self.db_path = db_path or str(DB_PATH)
        self.default_ttl = default_ttl_hours * 3600
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS cache_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cache_key TEXT UNIQUE NOT NULL,
            prompt TEXT,
            model TEXT DEFAULT '',
            provider TEXT DEFAULT '',
            response TEXT NOT NULL,
            tokens_used INTEGER DEFAULT 0,
            cost_saved REAL DEFAULT 0.0,
            hit_count INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME,
            tags TEXT DEFAULT '[]'
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_cache_key ON cache_entries(cache_key)")
        conn.commit()
        conn.close()
    
    def _make_key(self, prompt, model="", provider=""):
        """Generate cache key from prompt + model + provider."""
        raw = f"{prompt}|{model}|{provider}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]
    
    def get(self, prompt, model="", provider=""):
        """Get cached response. Returns None if miss/expired."""
        key = self._make_key(prompt, model, provider)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "SELECT response, tokens_used, hit_count FROM cache_entries WHERE cache_key = ? AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)",
            (key,)
        )
        row = c.fetchone()
        if row:
            c.execute(
                "UPDATE cache_entries SET hit_count = hit_count + 1, last_accessed = CURRENT_TIMESTAMP WHERE cache_key = ?",
                (key,)
            )
            conn.commit()
            conn.close()
            return {"response": row[0], "tokens_saved": row[1], "hit_count": row[2] + 1}
        conn.close()
        return None
    
    def set(self, prompt, response, model="", provider="", tokens_used=0, cost_saved=0.0, ttl_hours=None, tags=None):
        """Cache an LLM response."""
        key = self._make_key(prompt, model, provider)
        ttl = (ttl_hours * 3600) if ttl_hours else self.default_ttl
        expires = (datetime.now() + timedelta(seconds=ttl)).isoformat()
        tags = tags or []
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""INSERT OR REPLACE INTO cache_entries 
            (cache_key, prompt, model, provider, response, tokens_used, cost_saved, expires_at, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (key, prompt[:500], model, provider, response, tokens_used, cost_saved, expires, json.dumps(tags))
        )
        conn.commit()
        conn.close()
        return key
    
    def stats(self):
        """Get cache statistics."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM cache_entries")
        total = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM cache_entries WHERE expires_at > CURRENT_TIMESTAMP OR expires_at IS NULL")
        valid = c.fetchone()[0]
        c.execute("SELECT SUM(hit_count) FROM cache_entries")
        total_hits = c.fetchone()[0] or 0
        c.execute("SELECT SUM(cost_saved) FROM cache_entries")
        total_saved = c.fetchone()[0] or 0.0
        c.execute("SELECT SUM(tokens_used) FROM cache_entries")
        total_tokens = c.fetchone()[0] or 0
        conn.close()
        return {
            "total_entries": total,
            "valid_entries": valid,
            "total_hits": total_hits,
            "total_tokens_saved": total_tokens,
            "total_cost_saved": round(total_saved, 4),
        }
    
    def cleanup(self):
        """Remove expired entries."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM cache_entries WHERE expires_at < CURRENT_TIMESTAMP")
        deleted = c.rowcount
        conn.commit()
        conn.close()
        return {"expired_removed": deleted}
    
    def clear(self):
        """Clear all cache."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM cache_entries")
        deleted = c.rowcount
        conn.commit()
        conn.close()
        return {"cleared": deleted}
    
    def search(self, query, limit=10):
        """Search cached responses."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "SELECT cache_key, prompt, model, provider, response, hit_count, created_at FROM cache_entries WHERE prompt LIKE ? ORDER BY hit_count DESC LIMIT ?",
            (f"%{query}%", limit)
        )
        rows = c.fetchall()
        conn.close()
        return [{"key": r[0], "prompt": r[1], "model": r[2], "provider": r[3], "response": r[4][:200], "hits": r[5], "created": r[6]} for r in rows]


_cache = None

def get_cache(db_path=None):
    global _cache
    if _cache is None:
        _cache = Cache(db_path)
    return _cache


if __name__ == "__main__":
    c = get_cache()
    c.set("What is CTZ?", "CTZ is CHAOS TYPE ZERO", model="qwen3", provider="ollama", tokens_used=50)
    result = c.get("What is CTZ?", model="qwen3", provider="ollama")
    print(f"Cache hit: {result}")
    print(f"Stats: {c.stats()}")
