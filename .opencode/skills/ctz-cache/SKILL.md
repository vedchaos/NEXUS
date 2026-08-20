---
name: ctz-cache
description: LLM response caching strategies using ctz_cache_get/set/stats tools
---

# CTZ Cache Skill

## When to Use
- Caching LLM responses to avoid redundant calls
- Retrieving cached responses for相同 prompts
- Monitoring cache hit/miss statistics

## Available Tools
- ctz_cache_get: Retrieve cached response by prompt key
- ctz_cache_set: Store LLM response in cache
- ctz_cache_stats: Get cache statistics (hits, misses, size)

## Workflow
1. Before calling LLM, check cache with ctz_cache_get
2. If cache hit, use cached response
3. If cache miss, call LLM and store result with ctz_cache_set
4. Monitor performance with ctz_cache_stats

## Examples
- "user request" → "Ask same question again" → ctz_cache_get first, then ctz_api_post if miss
- "user request" → "How's cache performing?" → ctz_cache_stats
- "user request" → "Cache this response" → ctz_cache_set with prompt and response

## Notes
- Cache keys are based on prompt content
- TTL (time-to-live) can be set per entry
- Cache persists across sessions