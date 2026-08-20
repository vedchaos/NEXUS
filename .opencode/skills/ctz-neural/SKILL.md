---
name: ctz-neural
description: CHAOS TYPE ZERO Neural Network — text classification, summarization, embeddings, similarity, pattern detection, and batch categorization via TF-IDF and cosine similarity.
---

# CTZ Neural Network Skill

On-device ML inference for text analysis. No external dependencies — TF-IDF, cosine similarity, n-gram analysis.

## Available Tools

### ctz_neural_classify
Classify text into topic, sentiment, and intent.

```
ctz_neural_classify(text="The AI software crashed the server")
```

Returns: `{category, confidence, sentiment, sentiment_score, topic_scores}`

### ctz_neural_summarize
Extractive summarization — picks the most informative sentences.

```
ctz_neural_summarize(text="Long text here...", max_sentences=3)
```

### ctz_neural_embed
Generate TF-IDF embedding vector. Optionally pass a corpus for proper IDF weighting.

```
ctz_neural_embed(text="Some text")
ctz_neural_embed(text="Some text", corpus=["doc1", "doc2", "doc3"])
```

### ctz_neural_similarity
Score similarity between two texts (0.0 = unrelated, 1.0 = identical).

```
ctz_neural_similarity(text1="The cat sat on the mat", text2="A cat sitting on a mat")
```

### ctz_neural_patterns
Detect frequent words, common bigrams, length stats, and shared characters across a batch.

```
ctz_neural_patterns(texts=["text1", "text2", "text3"])
```

### ctz_neural_categorize
Batch-categorize texts by topic with confidence and sentiment per item.

```
ctz_neural_categorize(texts=["tech news", "sports update", "health tip"])
```

## Workflow

1. **Classify** incoming text to understand topic and sentiment
2. **Summarize** long content for quick overview
3. **Embed** texts for vector-based operations
4. **Similarity** to compare two pieces of text
5. **Patterns** to analyze batches for recurring themes
6. **Categorize** to sort a collection of texts into topics

## Notes

- All inference runs on-device via `bridge_core/neural.py` — no API calls
- Embeddings are TF-IDF based; pass a corpus for meaningful IDF values
- Classification logs results to `data/neural/neural.db`
