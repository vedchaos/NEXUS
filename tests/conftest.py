"""Pytest configuration."""
import pytest


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


@pytest.fixture
def sample_task():
    """Sample task for testing."""
    return {
        "type": "code",
        "prompt": "Write a hello world function",
        "context": {},
        "priority": "medium"
    }


@pytest.fixture
def sample_memory():
    """Sample memory entry for testing."""
    return {
        "type": "fact",
        "content": "CTZ has 14 LLM providers",
        "importance": 0.7,
        "timestamp": "2026-08-20T00:00:00"
    }
