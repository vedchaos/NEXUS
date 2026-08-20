"""Tests for smart_brain module."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bridge_core.smart_brain import SmartBrain


class TestSmartBrain:
    """Test SmartBrain initialization and basic operations."""

    def test_init(self):
        """SmartBrain should initialize without errors."""
        brain = SmartBrain()
        assert brain is not None

    def test_has_query(self):
        """SmartBrain should have query method."""
        brain = SmartBrain()
        assert callable(getattr(brain, 'query', None))

    def test_has_select_model(self):
        """SmartBrain should have select_model method."""
        brain = SmartBrain()
        assert callable(getattr(brain, 'select_model', None))

    def test_has_select_provider(self):
        """SmartBrain should have select_provider method."""
        brain = SmartBrain()
        assert callable(getattr(brain, 'select_provider', None))

    def test_has_cache(self):
        """SmartBrain should have cache."""
        brain = SmartBrain()
        assert hasattr(brain, 'cache')

    def test_has_stats(self):
        """SmartBrain should track usage stats."""
        brain = SmartBrain()
        stats = brain.get_stats()
        assert stats is not None

    def test_usage_tracking(self):
        """SmartBrain should track usage."""
        brain = SmartBrain()
        assert hasattr(brain, 'usage')
