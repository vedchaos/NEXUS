#!/usr/bin/env python3
"""CHAOS TYPE ZERO Meta-Reasoner — Intelligent task routing and strategy selection"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path

CTZ_ROOT = Path(__file__).parent.parent
DATA_DIR = CTZ_ROOT / "data" / "meta_reasoner"
DB_PATH = DATA_DIR / "meta_reasoner.db"
DATA_DIR.mkdir(parents=True, exist_ok=True)

STRATEGIES = {
    "fast_local": {"provider": "ollama", "model": "llama3.1", "description": "Fast local, zero cost",
                   "strengths": ["speed", "privacy", "cost"], "weaknesses": ["quality"], "complexity_cap": 5},
    "balanced_free": {"provider": "groq", "model": "llama-3.1-8b-instant", "description": "Free fast cloud",
                      "strengths": ["speed", "cost"], "weaknesses": ["rate_limits"], "complexity_cap": 6},
    "quality_cloud": {"provider": "openai", "model": "gpt-4o", "description": "High quality cloud",
                      "strengths": ["quality", "reasoning"], "weaknesses": ["cost"], "complexity_cap": 10},
    "deep_reasoning": {"provider": "anthropic", "model": "claude-3-sonnet-20240229", "description": "Deep analysis",
                       "strengths": ["reasoning", "quality"], "weaknesses": ["cost", "speed"], "complexity_cap": 10},
    "code_specialist": {"provider": "deepseek", "model": "deepseek-chat", "description": "Code specialist",
                        "strengths": ["code", "cost"], "weaknesses": ["general"], "complexity_cap": 8},
}


class CTZMetaReasoner:
    """Intelligent task routing and strategy selection for CHAOS TYPE ZERO."""
    def __init__(self, db_path=None):
        self.db_path = db_path or str(DB_PATH)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, strategy_id TEXT NOT NULL,
            task_type TEXT DEFAULT '', success INTEGER DEFAULT 1,
            duration_s REAL DEFAULT 0.0, tokens_used INTEGER DEFAULT 0,
            error_msg TEXT DEFAULT '', created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("""CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, task_type TEXT NOT NULL,
            strategy_id TEXT NOT NULL, score REAL DEFAULT 0.5,
            hit_count INTEGER DEFAULT 1, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_outcome_strategy ON outcomes(strategy_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_rec_type ON recommendations(task_type)")
        conn.commit()
        conn.close()

    def _get_complexity(self, task_desc):
        lower = task_desc.lower()
        word_count = len(lower.split())
        indicators = sum(1 for w in ["why", "explain", "analyze", "compare",
                                      "evaluate", "design", "architect", "optimize", "refactor"] if w in lower)
        if word_count <= 5 and indicators == 0:
            return 2
        if word_count <= 15 and indicators <= 1:
            return 4
        if word_count <= 30 and indicators <= 2:
            return 6
        if indicators >= 3 or word_count > 40:
            return 9
        return 5

    def _time_context(self):
        hour = datetime.now().hour
        if 2 <= hour < 6:
            return "night", 0.7
        if 6 <= hour < 10:
            return "morning", 1.0
        if 10 <= hour < 14:
            return "midday", 1.1
        if 14 <= hour < 18:
            return "afternoon", 1.0
        if 18 <= hour < 22:
            return "evening", 0.9
        return "night", 0.7

    def plan(self, task, context=None):
        context = context or {}
        task_desc = str(task)
        complexity = context.get("complexity", self._get_complexity(task_desc))
        task_type = context.get("task_type", "general")
        _, load_factor = self._time_context()
        strategies = []
        for sid, info in STRATEGIES.items():
            if complexity > info.get("complexity_cap", 10):
                continue
            stats = self._get_strategy_stats(sid)
            success_rate = stats.get("success_rate", 0.5)
            avg_duration = stats.get("avg_duration", 10.0)
            score = 0.5
            if complexity <= 3 and "speed" in info.get("strengths", []):
                score += 0.2
            if complexity >= 7 and "reasoning" in info.get("strengths", []):
                score += 0.2
            if task_type == "code" and "code" in info.get("strengths", []):
                score += 0.15
            score += success_rate * 0.15
            if avg_duration < 5:
                score += 0.05
            score *= load_factor
            if info.get("provider") == "ollama":
                score += 0.05
            score = max(0.0, min(1.0, score))
            strategies.append({
                "strategy_id": sid, "description": info["description"],
                "provider": info["provider"], "model": info["model"],
                "score": round(score, 3),
                "confidence": round(success_rate * load_factor, 3),
                "complexity_fit": max(0, 1 - (complexity - info.get("complexity_cap", 10)) / 10),
            })
        strategies.sort(key=lambda s: s["score"], reverse=True)
        return strategies

    def select_strategy(self, strategies):
        return strategies[0] if strategies else None

    def record_outcome(self, strategy_id, success, metrics=None):
        metrics = metrics or {}
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""INSERT INTO outcomes 
            (strategy_id, task_type, success, duration_s, tokens_used, error_msg)
            VALUES (?, ?, ?, ?, ?, ?)""",
                  (strategy_id, metrics.get("task_type", ""), 1 if success else 0,
                   metrics.get("duration_s", 0), metrics.get("tokens_used", 0), metrics.get("error", "")))
        conn.commit()
        conn.close()

    def get_recommendation(self, task_type):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""SELECT strategy_id, score, hit_count FROM recommendations 
            WHERE task_type = ? ORDER BY score DESC LIMIT 1""", (task_type,))
        row = c.fetchone()
        conn.close()
        if row:
            return {"strategy_id": row[0], "score": row[1], "hit_count": row[2]}
        stats = self._get_all_strategy_stats()
        if stats:
            best = max(stats.items(), key=lambda x: x[1].get("success_rate", 0))
            return {"strategy_id": best[0], "score": best[1].get("success_rate", 0.5),
                    "hit_count": best[1].get("count", 0)}
        return {"strategy_id": "balanced_free", "score": 0.5, "hit_count": 0}

    def _get_strategy_stats(self, strategy_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""SELECT COUNT(*), SUM(success), AVG(duration_s) 
            FROM outcomes WHERE strategy_id = ?""", (strategy_id,))
        row = c.fetchone()
        conn.close()
        count = row[0] or 0
        return {"count": count, "success_rate": (row[1] or 0) / count if count else 0.5,
                "avg_duration": row[2] or 0.0}

    def _get_all_strategy_stats(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""SELECT strategy_id, COUNT(*), SUM(success), AVG(duration_s)
            FROM outcomes GROUP BY strategy_id""")
        rows = c.fetchall()
        conn.close()
        stats = {}
        for sid, count, success_sum, avg_dur in rows:
            stats[sid] = {"count": count, "success_rate": (success_sum or 0) / count if count else 0.5,
                          "avg_duration": avg_dur or 0.0}
        return stats

    def get_stats(self):
        stats = self._get_all_strategy_stats()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM outcomes")
        total = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM outcomes WHERE success = 1")
        total_success = c.fetchone()[0]
        conn.close()
        return {"total_outcomes": total,
                "overall_success_rate": round(total_success / total if total else 0.5, 3),
                "strategies": stats, "available_strategies": list(STRATEGIES.keys())}

    def adapt_route(self, task, current_strategy):
        strategies = self.plan(task)
        current_stats = self._get_strategy_stats(current_strategy)
        if current_stats["count"] >= 5 and current_stats["success_rate"] < 0.6:
            alternatives = [s for s in strategies if s["strategy_id"] != current_strategy]
            if alternatives:
                best_alt = alternatives[0]
                return {"should_switch": True,
                        "reason": f"Strategy '{current_strategy}' at {current_stats['success_rate']:.0%} success",
                        "recommended": best_alt["strategy_id"],
                        "expected_improvement": round(best_alt["score"] - current_stats["success_rate"], 3)}
        best = strategies[0] if strategies else None
        if best and best["strategy_id"] != current_strategy and best["score"] > 0.1:
            return {"should_switch": False, "current_is_best": False,
                    "recommended": best["strategy_id"], "reason": "Performing adequately"}
        return {"should_switch": False, "current_is_best": True, "reason": "Current strategy is optimal"}


_meta_reasoner = None

def get_meta_reasoner(db_path=None):
    global _meta_reasoner
    if _meta_reasoner is None:
        _meta_reasoner = CTZMetaReasoner(db_path)
    return _meta_reasoner

if __name__ == "__main__":
    mr = get_meta_reasoner()
    strats = mr.plan("Explain how neural network backpropagation works")
    print("Strategies:")
    for s in strats:
        print(f"  {s['strategy_id']}: score={s['score']}, confidence={s['confidence']}")
    best = mr.select_strategy(strats)
    print(f"\nSelected: {best['strategy_id']}")
    mr.record_outcome("balanced_free", True, {"duration_s": 3.2, "task_type": "explanation"})
    print(json.dumps(mr.get_stats(), indent=2))
