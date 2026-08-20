#!/usr/bin/env python3
"""
CHAOS TYPE ZERO Vault — Secure Credential Management
Encrypt and manage API keys, tokens, secrets.

Features:
- XOR encryption for stored secrets
- Access logging
- Secret categories
- Auto-redaction in logs
"""

import base64
import hashlib
import json
import os
import sqlite3
import time
from pathlib import Path

CTZ_ROOT = Path(__file__).parent.parent
DATA_DIR = CTZ_ROOT / "data"
VAULT_DIR = DATA_DIR / "vault"
DB_PATH = VAULT_DIR / "vault.db"

VAULT_DIR.mkdir(parents=True, exist_ok=True)

# Simple obfuscation key (not military-grade, but keeps secrets out of plain text)
_OBFUSC_KEY = b"CTZ_VAULT_2026_CHAOS_TYPE_ZERO"


def _xor_bytes(data, key):
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def _encrypt(plaintext):
    encrypted = _xor_bytes(plaintext.encode(), _OBFUSC_KEY)
    return base64.b64encode(encrypted).decode()


def _decrypt(ciphertext):
    decrypted = _xor_bytes(base64.b64decode(ciphertext), _OBFUSC_KEY)
    return decrypted.decode()


class Vault:
    def __init__(self, db_path=None):
        self.db_path = db_path or str(DB_PATH)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS secrets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            value_encrypted TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            description TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_accessed DATETIME,
            access_count INTEGER DEFAULT 0
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS access_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            secret_name TEXT,
            action TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
        conn.commit()
        conn.close()
    
    def set(self, name, value, category="general", description=""):
        encrypted = _encrypt(value)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO secrets (name, value_encrypted, category, description) VALUES (?, ?, ?, ?)",
                  (name, encrypted, category, description))
        c.execute("INSERT INTO access_log (secret_name, action) VALUES (?, 'set')", (name,))
        conn.commit()
        conn.close()
        return {"status": "stored", "name": name}
    
    def get(self, name):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT value_encrypted, category, description FROM secrets WHERE name = ?", (name,))
        row = c.fetchone()
        if row:
            c.execute("UPDATE secrets SET last_accessed = CURRENT_TIMESTAMP, access_count = access_count + 1 WHERE name = ?", (name,))
            c.execute("INSERT INTO access_log (secret_name, action) VALUES (?, 'get')", (name,))
            conn.commit()
            conn.close()
            return {"name": name, "value": _decrypt(row[0]), "category": row[1], "description": row[2]}
        conn.close()
        return None
    
    def delete(self, name):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM secrets WHERE name = ?", (name,))
        c.execute("INSERT INTO access_log (secret_name, action) VALUES (?, 'delete')", (name,))
        conn.commit()
        conn.close()
        return {"status": "deleted", "name": name}
    
    def list_all(self, category=None):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        if category:
            c.execute("SELECT name, category, description, access_count FROM secrets WHERE category = ?", (category,))
        else:
            c.execute("SELECT name, category, description, access_count FROM secrets")
        rows = c.fetchall()
        conn.close()
        return [{"name": r[0], "category": r[1], "description": r[2], "access_count": r[3]} for r in rows]
    
    def stats(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM secrets")
        total = c.fetchone()[0]
        c.execute("SELECT category, COUNT(*) FROM secrets GROUP BY category")
        cats = {r[0]: r[1] for r in c.fetchall()}
        c.execute("SELECT COUNT(*) FROM access_log")
        logs = c.fetchone()[0]
        conn.close()
        return {"total_secrets": total, "categories": cats, "access_logs": logs}


_vault = None

def get_vault():
    global _vault
    if _vault is None:
        _vault = Vault()
    return _vault


if __name__ == "__main__":
    v = get_vault()
    v.set("test_key", "super_secret_123", category="api", description="Test key")
    print("Get:", v.get("test_key"))
    print("List:", v.list_all())
    print("Stats:", v.stats())
    v.delete("test_key")
