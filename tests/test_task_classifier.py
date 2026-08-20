"""Tests for task classifier."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bridge_core.task_classifier import classify_task, get_task_chain


class TestClassifyTask:
    """Test task classification function."""

    def test_classify_code(self):
        """Should classify code tasks."""
        result = classify_task("Write a Python function")
        assert result is not None

    def test_classify_security(self):
        """Should classify security tasks."""
        result = classify_task("Scan for vulnerabilities")
        assert result is not None

    def test_classify_research(self):
        """Should classify research tasks."""
        result = classify_task("Research latest AI trends")
        assert result is not None

    def test_classify_memory(self):
        """Should classify memory tasks."""
        result = classify_task("Save this information for later")
        assert result is not None

    def test_classify_automation(self):
        """Should classify automation tasks."""
        result = classify_task("Automate this workflow")
        assert result is not None


class TestGetTaskChain:
    """Test task chain function."""

    def test_chain_code(self):
        """get_task_chain should return chain for code task."""
        chain = get_task_chain("code")
        assert chain is not None

    def test_chain_security(self):
        """get_task_chain should return chain for security task."""
        chain = get_task_chain("security")
        assert chain is not None

    def test_chain_research(self):
        """get_task_chain should return chain for research task."""
        chain = get_task_chain("research")
        assert chain is not None

    def test_chain_automation(self):
        """get_task_chain should return chain for automation task."""
        chain = get_task_chain("automation")
        assert chain is not None
