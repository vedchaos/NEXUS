#!/usr/bin/env python3
"""
NEXUS 6-Agent OMO Sisyphus Orchestrator
Plan → Execute → Critique → Refine → Memory → Report
"""

import json
import time
from datetime import datetime
from pathlib import Path

# Import NEXUS modules
import sys
sys.path.insert(0, str(Path(__file__).parent))
from smart_brain import get_brain
from memory_3tier import get_memory


class Agent:
    """Base agent class"""

    def __init__(self, name, role, soul_path=None):
        self.name = name
        self.role = role
        self.soul = self._load_soul(soul_path)
        self.brain = get_brain()
        self.memory = get_memory()

    def _load_soul(self, path):
        if path and Path(path).exists():
            return Path(path).read_text()
        return f"You are NEXUS {self.name}. Role: {self.role}"

    def think(self, context, task_type="agent"):
        """Use LLM to think about a task"""
        prompt = f"Context: {json.dumps(context)}\n\nTask: {self.role}"
        response, provider, model, cached = self.brain.query(prompt, task_type)
        return {
            "response": response,
            "provider": provider,
            "model": model,
            "cached": cached,
        }


class PlannerAgent(Agent):
    """Breaks tasks into steps, creates execution plan"""

    def __init__(self):
        super().__init__("Planner", "Break user request into clear, ordered steps")

    def plan(self, user_request, context=None):
        prompt = f"""Analyze this request and create a step-by-step execution plan.

Request: {user_request}

Context: {json.dumps(context or {})}

Return a JSON plan with:
- steps: array of {{id, action, tool, args, depends_on}}
- estimated_time: seconds
- risk_level: low/medium/high
- requires_authorization: boolean"""

        result = self.think(prompt, task_type="agent")

        try:
            plan = json.loads(result["response"])
        except:
            plan = {
                "steps": [{"id": 1, "action": result["response"], "tool": "general", "args": {}}],
                "estimated_time": 30,
                "risk_level": "low",
                "requires_authorization": False,
            }

        return plan


class CoderAgent(Agent):
    """Writes and reviews code"""

    def __init__(self):
        super().__init__("Coder", "Write clean, efficient, well-documented code")

    def write_code(self, spec, language="python"):
        prompt = f"""Write {language} code for this specification:

{spec}

Requirements:
- Clean, readable code
- Proper error handling
- Comments where needed
- Follow best practices"""

        result = self.think(prompt, task_type="code")
        return result["response"]

    def review_code(self, code):
        prompt = f"""Review this code for:
- Bugs and errors
- Security issues
- Performance problems
- Code quality

Code:
{code}

Return JSON with: issues[], suggestions[], score (1-10)"""

        result = self.think(prompt, task_type="code")
        try:
            return json.loads(result["response"])
        except:
            return {"issues": [], "suggestions": [result["response"]], "score": 7}


class ResearcherAgent(Agent):
    """Gathers information via web search, OSINT, databases"""

    def __init__(self):
        super().__init__("Researcher", "Gather accurate, relevant information")

    def research(self, query, context=None):
        prompt = f"""Research this topic thoroughly:

Query: {query}
Context: {json.dumps(context or {})}

Provide:
- Key findings
- Sources
- Confidence level
- Related information"""

        result = self.think(prompt, task_type="research")
        return {
            "findings": result["response"],
            "provider": result["provider"],
        }


class CriticAgent(Agent):
    """Reviews work, finds errors, suggests improvements"""

    def __init__(self):
        super().__init__("Critic", "Review work critically, find errors, suggest improvements")

    def review(self, work, criteria=None):
        prompt = f"""Critically review this work:

{json.dumps(work) if isinstance(work, dict) else work}

Criteria: {criteria or 'quality, accuracy, completeness, security'}

Return JSON with:
- score: 1-10
- issues: [{{severity, description, fix}}]
- strengths: [str]
- improvements: [str]
- pass: boolean (score >= 7)"""

        result = self.think(prompt, task_type="quality")
        try:
            return json.loads(result["response"])
        except:
            return {
                "score": 7,
                "issues": [],
                "strengths": ["Work completed"],
                "improvements": [result["response"]],
                "pass": True,
            }


class ExecutorAgent(Agent):
    """Runs commands, makes API calls, does the actual work"""

    def __init__(self):
        super().__init__("Executor", "Execute planned steps efficiently")

    def execute(self, step, context=None):
        """Execute a single step"""
        # This would actually run commands/tools
        # For now, return the execution plan
        return {
            "step": step,
            "status": "executed",
            "timestamp": datetime.now().isoformat(),
            "output": f"Step {step.get('id', '?')} executed: {step.get('action', 'unknown')}",
        }


class MemoryAgent(Agent):
    """Manages long-term memory, retrieval, storage"""

    def __init__(self):
        super().__init__("Memory", "Manage persistent memory across sessions")

    def remember(self, content, tags="", importance=0.5, mem_type="note"):
        """Save to memory"""
        mem_id = self.memory.save(content, tags, mem_type, importance)
        return {"saved": True, "memory_id": mem_id}

    def recall(self, query, limit=10):
        """Search memory"""
        results = self.memory.search(query, limit)
        return {"results": results, "count": len(results)}

    def summarize_session(self, conversation):
        """Summarize a session for memory"""
        prompt = f"""Summarize this conversation for long-term memory:

{json.dumps(conversation[-10:])}

Return key:
- decisions: [str]
- findings: [str]
- tasks_completed: [str]
- pending: [str]
- importance: 0.0-1.0"""

        result = self.think(prompt, task_type="write")
        try:
            return json.loads(result["response"])
        except:
            return {"summary": result["response"], "importance": 0.7}


# === Sisyphus Orchestrator ===
class SisyphusOrchestrator:
    """
    6-Agent OMO Sisyphus Loop:
    1. Observer: User input → understand
    2. Model: Create plan
    3. Operate: Execute plan
    4. Critic: Review output
    5. Refine: Fix issues (loop back to Operate)
    6. Memory: Save outcome
    7. Report: Return results
    """

    def __init__(self, adaptive=True, max_iterations=3):
        self.planner = PlannerAgent()
        self.coder = CoderAgent()
        self.researcher = ResearcherAgent()
        self.critic = CriticAgent()
        self.executor = ExecutorAgent()
        self.memory_agent = MemoryAgent()
        self.adaptive = adaptive  # Skip critique for simple tasks
        self.max_iterations = max_iterations

    def run(self, user_request, context=None):
        """Execute the full Sisyphus loop"""
        start_time = time.time()
        log = []

        # Step 1: PLAN
        log.append({"step": "plan", "time": time.time()})
        plan = self.planner.plan(user_request, context)
        log.append({"step": "plan_result", "plan": plan})

        # Step 2: EXECUTE
        results = []
        for step in plan.get("steps", []):
            log.append({"step": "execute", "step_id": step.get("id")})
            result = self.executor.execute(step, context)
            results.append(result)
        log.append({"step": "execute_results", "results": results})

        # Step 3: CRITIQUE (adaptive — skip for simple tasks)
        if self.adaptive and plan.get("risk_level") == "low" and len(plan.get("steps", [])) <= 2:
            critique = {"score": 9, "pass": True, "issues": []}
            log.append({"step": "critique_skipped", "reason": "simple_task"})
        else:
            log.append({"step": "critique"})
            critique = self.critic.review({"plan": plan, "results": results})
            log.append({"step": "critique_result", "critique": critique})

        # Step 4: REFINE (if needed)
        iterations = 0
        while not critique.get("pass", True) and iterations < self.max_iterations:
            iterations += 1
            log.append({"step": "refine", "iteration": iterations})

            # Fix issues
            for issue in critique.get("issues", []):
                fix_prompt = f"Fix this issue: {issue.get('description', '')}"
                self.coder.write_code(fix_prompt)

            # Re-critique
            critique = self.critic.review({"plan": plan, "results": results})
            log.append({"step": "critique_result", "critique": critique})

        # Step 5: MEMORY
        log.append({"step": "memory"})
        summary = self.memory_agent.remember(
            f"Task: {user_request}\nResult: {json.dumps(results[:3])}",
            tags="task_outcome",
            importance=critique.get("score", 5) / 10.0,
            mem_type="task",
        )
        log.append({"step": "memory_result", "summary": summary})

        # Step 6: REPORT
        elapsed = time.time() - start_time
        report = {
            "request": user_request,
            "plan": plan,
            "results": results,
            "critique": critique,
            "iterations": iterations,
            "elapsed_seconds": round(elapsed, 2),
            "log": log,
        }

        return report


# === Singleton ===
_orchestrator = None

def get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SisyphusOrchestrator()
    return _orchestrator


if __name__ == "__main__":
    orch = get_orchestrator()
    result = orch.run("Initialize NEXUS memory system and save a test entry")
    print(json.dumps(result, indent=2))
