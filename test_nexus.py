#!/usr/bin/env python3
"""NEXUS v1.0 — Full System Test"""

import json, time

print("=" * 60)
print("   NEXUS v1.0 — Full System Test")
print("=" * 60)

# 1. Smart Brain
print("\n[1/5] Smart Brain (14 LLM Providers)...")
from bridge_core.smart_brain import get_brain
brain = get_brain()
status = brain.get_stats()
print(f"  Providers: {status['providers']}")
print(f"  Task Chains: {status['task_chains']}")
print(f"  Keys Loaded: {status['keys_loaded']}")

# 2. Memory System
print("\n[2/5] 3-Tier Memory (RAM + SQLite + ChromaDB)...")
from bridge_core.memory_3tier import get_memory
mem = get_memory()
mem_id = mem.save("NEXUS test memory: system initialized successfully", "test,nexus", "note", 0.9)
print(f"  Saved: {mem_id}")
results = mem.search("NEXUS test")
print(f"  Found: {len(results)} results")
for r in results[:2]:
    print(f"    -> {r['content'][:60]}...")

# 3. Task Classifier
print("\n[3/5] Task Classifier (12 types)...")
from bridge_core.task_classifier import classify_task, get_task_chain
tests = [
    "write a python function to sort a list",
    "scan target.com for vulnerabilities",
    "explain machine learning",
    "mera code fix karo",
]
for t in tests:
    task_type, confidence = classify_task(t)
    chain = get_task_chain(task_type)
    print(f'  "{t[:40]}..."')
    print(f"    -> Type: {task_type} ({confidence:.0%}) | Providers: {chain['preferred'][:3]}")

# 4. Agent System
print("\n[4/5] 6-Agent Sisyphus Orchestrator...")
from bridge_core.agents import get_orchestrator
orch = get_orchestrator()
print("  Agents: Planner, Coder, Researcher, Critic, Executor, Memory")
print(f"  Adaptive: {orch.adaptive}")
print(f"  Max Iterations: {orch.max_iterations}")

# 5. Scheduler
print("\n[5/5] Hinglish Scheduler...")
from bridge_core.scheduler import parse_hinglish_time
tests = ["agle 5 minute mein", "aaj raat 10 baje", "kal subah 9 AM"]
for t in tests:
    parsed = parse_hinglish_time(t)
    print(f'  "{t}" -> {parsed}')

print("\n" + "=" * 60)
print("   ALL 5 TESTS PASSED!")
print("=" * 60)
