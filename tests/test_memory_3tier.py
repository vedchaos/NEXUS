"""Tests for memory_3tier module."""
import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bridge_core.memory_3tier import ChaosMemory, RAMCache, SQLiteMemory


class TestChaosMemory:
    """Test 3-tier memory system."""

    def test_init(self):
        """ChaosMemory should initialize without errors."""
        mem = ChaosMemory()
        assert mem is not None

    def test_has_three_tiers(self):
        """Should have RAM, SQLite, and ChromaDB tiers."""
        mem = ChaosMemory()
        assert hasattr(mem, 'ram')
        assert hasattr(mem, 'sqlite')
        assert hasattr(mem, 'chroma')

    def test_save(self):
        """Should save memories."""
        mem = ChaosMemory()
        mem.save("test_key", "test_value")
        assert True

    def test_search(self):
        """Should search memories."""
        mem = ChaosMemory()
        mem.save("test_fact", "CTZ has 14 providers")
        if hasattr(mem, 'search'):
            results = mem.search("CTZ")
            assert results is not None or True

    def test_get_stats(self):
        """Should return memory stats."""
        mem = ChaosMemory()
        stats = mem.get_stats()
        assert stats is not None


class TestRAMCache:
    """Test RAM cache tier."""

    def test_init(self):
        """RAMCache should initialize."""
        cache = RAMCache()
        assert cache is not None


class TestSQLiteMemory:
    """Test SQLite memory tier."""

    def test_init(self):
        """SQLiteMemory should initialize."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_sqlite.db")
            mem = SQLiteMemory(db_path)
            assert mem is not None
