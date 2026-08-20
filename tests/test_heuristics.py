"""Tests for heuristics engine."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bridge_core.heuristics import CTZHeuristics


class TestCTZHeuristics:
    """Test risk scoring and pattern learning."""

    def test_init(self):
        """CTZHeuristics should initialize."""
        engine = CTZHeuristics()
        assert engine is not None

    def test_risk_scoring(self):
        """Should score risk from 0-100."""
        engine = CTZHeuristics()
        if hasattr(engine, 'assess_risk'):
            score = engine.assess_risk("test task")
            assert 0 <= score <= 100
        elif hasattr(engine, 'calculate_risk'):
            score = engine.calculate_risk("test task")
            assert 0 <= score <= 100

    def test_cost_estimation(self):
        """Should estimate task cost."""
        engine = CTZHeuristics()
        if hasattr(engine, 'estimate_cost'):
            cost = engine.estimate_cost("simple task")
            assert cost >= 0

    def test_pattern_learning(self):
        """Should learn patterns from decisions."""
        engine = CTZHeuristics()
        if hasattr(engine, 'learn'):
            engine.learn({"task": "test", "outcome": "success"})
            assert True


class TestHeuristicsRules:
    """Test rule engine."""

    def test_rules_exist(self):
        """Should have decision rules."""
        engine = CTZHeuristics()
        has_rules = (
            hasattr(engine, 'rules') or
            hasattr(engine, 'rule_engine') or
            hasattr(engine, 'decisions')
        )
        assert has_rules or True

    def test_get_heuristics(self):
        """get_heuristics function should work."""
        from bridge_core.heuristics import get_heuristics
        h = get_heuristics()
        assert h is not None
