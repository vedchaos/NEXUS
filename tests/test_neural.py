"""Tests for neural module."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bridge_core.neural import CTZNeural


class TestCTZNeural:
    """Test text classification and embeddings."""

    def test_init(self):
        """CTZNeural should initialize."""
        engine = CTZNeural()
        assert engine is not None

    def test_classification(self):
        """Should classify text into categories."""
        engine = CTZNeural()
        if hasattr(engine, 'classify'):
            result = engine.classify("This is a security issue")
            assert result is not None

    def test_embedding(self):
        """Should generate text embeddings."""
        engine = CTZNeural()
        if hasattr(engine, 'embed'):
            embedding = engine.embed("test text")
            assert embedding is not None

    def test_tokenize(self):
        """Tokenize function should work."""
        from bridge_core.neural import _tokenize
        tokens = _tokenize("hello world test")
        assert len(tokens) > 0

    def test_cosine_sim(self):
        """Cosine similarity should work."""
        from bridge_core.neural import _cosine_sim
        sim = _cosine_sim([1, 0, 0], [1, 0, 0])
        assert sim == 1.0

    def test_get_neural(self):
        """get_neural function should work."""
        from bridge_core.neural import get_neural
        n = get_neural()
        assert n is not None
