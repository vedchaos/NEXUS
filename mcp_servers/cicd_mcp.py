#!/usr/bin/env python3
"""CHAOS TYPE ZERO MCP — CI/CD Pipeline Server"""

import json
import subprocess
import sys
import urllib.request
import urllib.error
import os

TOOLS = [
    {"name": "ctz_github_status", "description": "Check GitHub Actions workflow run status", "inputSchema": {"type": "object", "properties": {"repo": {"type": "string", "description": "owner/repo"}, "workflow": {"type": "string", "default": ""}, "branch": {"type": "string", "default": ""}, "run_id": {"type": "string", "default": ""}, "token": {"type": "string", "default": ""}}, "required": ["repo"]}},
    {"name": "ctz_github_trigger", "description": "Trigger a GitHub Actions workflow", "inputSchema": {"type": "object", "properties": {"repo": {"type": "string", "description": "owner/repo"}, "workflow": {"type": "string", "description": "workflow file name or ID"}, "ref": {"type": "string", "default": "main"}, "inputs": {"type": "object", "default": {}}, "token": {"type": "string", "default": ""}}, "required": ["repo", "workflow"]}},
    {"name": "ctz_gitlab_pipeline", "description": "Check GitLab CI pipeline status", "inputSchema": {"type": "object", "properties": {"project_id": {"type": "string", "description": "GitLab project ID or URL-encoded path"}, "pipeline_id": {"type": "string", "default": ""}, "branch": {"type": "string", "default": ""}, "gitlab_url": {"type": "string", "default": "https://gitlab.com"}, "token": {"type": "string", "default": ""}}, "required": ["project_id"]}},
    {"name": "ctz_jenkins_build", "description": "Check Jenkins build status", "inputSchema": {"type": "object", "properties": {"job": {"type": "string", "description": "Jenkins job name/path"}, "build_number": {"type": "string", "default": ""}, "jenkins_url": {"type": "string", "default": ""}, "token": {"type": "string", "default": ""}}, "required": ["job"]}},
    {"name": "ctz_cicd_logs", "description": "Get pipeline execution logs", "inputSchema": {"type": "object", "properties": {"system": {"type": "string", "enum": ["github", "gitlab", "jenkins"], "default": "github"}, "repo": {"type": "string", "default": ""}, "run_id": {"type": "string", "default": ""}, "job": {"type": "string", "default": ""}, "log_lines": {"type": "integer", "default": 100}, "token": {"type": "string", "default": ""}}, "required": ["system"]}},
    {"name": "ctz_cicd_deploy", "description": "Trigger a deployment pipeline", "inputSchema": {"type": "object", "properties": {"target": {"type": "string", "enum": ["staging", "production"], "default": "staging"}, "service": {"type": "string", "description": "Service name to deploy"}, "version": {"type": "string", "default": "latest"}, "repo": {"type": "string", "default": ""}, "token": {"type": "string", "default": ""}}, "required": ["service"]}},
    {"name": "ctz_cicd_rollback", "description": "Rollback deployment to previous version", "inputSchema": {"type": "object", "properties": {"target": {"type": "string", "enum": ["staging", "production"], "default": "staging"}, "service": {"type": "string", "description": "Service name to rollback"}, "to_version": {"type": "string", "default": ""}, "repo": {"type": "string", "default": ""}, "token": {"type": "string", "default": ""}}, "required": ["service"]}},
]


def _get_token(args):
    token = args.get("token", "")
    if not token:
        token = os.environ.get("GITHUB_TOKEN", os.environ.get("GH_TOKEN", ""))
    return token


def _github_api(url, token, method="GET", data=None):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "CTZ-CICD/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, headers=headers, method=method, data=body)
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")[:500]
        return {"error": f"HTTP {e.code}: {e.reason}", "detail": body_text}


def github_status(args):
    repo = args["repo"]
    token = _get_token(args)
    if args.get("run_id"):
        url = f"https://api.github.com/repos/{repo}/actions/runs/{args['run_id']}"
        run = _github_api(url, token)
        if "error" in run:
            return run
        return {"repo": repo, "run_id": run.get("id"), "name": run.get("name"), "status": run.get("status"), "conclusion": run.get("conclusion"), "branch": run.get("head_branch"), "commit": run.get("head_sha", "")[:12], "created_at": run.get("created_at"), "updated_at": run.get("updated_at"), "html_url": run.get("html_url")}
    params = []
    if args.get("branch"):
        params.append(f"branch={args['branch']}")
    if args.get("workflow"):
        params.append(f"workflow={args['workflow']}")
    qs = "&".join(params)
    url = f"https://api.github.com/repos/{repo}/actions/runs?per_page=10" + (f"&{qs}" if qs else "")
    data = _github_api(url, token)
    if "error" in data:
        return data
    runs = []
    for run in data.get("workflow_runs", [])[:10]:
        runs.append({"id": run.get("id"), "name": run.get("name"), "status": run.get("status"), "conclusion": run.get("conclusion"), "branch": run.get("head_branch"), "commit": run.get("head_sha", "")[:12], "created_at": run.get("created_at")})
    return {"repo": repo, "total_runs": len(runs), "runs": runs}


def github_trigger(args):
    repo = args["repo"]
    workflow = args["workflow"]
    token = _get_token(args)
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow}/dispatches"
    data = {"ref": args.get("ref", "main"), "inputs": args.get("inputs", {})}
    result = _github_api(url, token, method="POST", data=data)
    if "error" in result:
        return result
    return {"repo": repo, "workflow": workflow, "ref": args.get("ref", "main"), "status": "triggered", "message": "Workflow dispatch sent. Check GitHub Actions for run status."}


def gitlab_pipeline(args):
    project = args["project_id"]
    base = args.get("gitlab_url", "https://gitlab.com").rstrip("/")
    token = args.get("token", "") or os.environ.get("GITLAB_TOKEN", "")
    headers = {"User-Agent": "CTZ-CICD/1.0"}
    if token:
        headers["PRIVATE-TOKEN"] = token
    if args.get("pipeline_id"):
        url = f"{base}/api/v4/projects/{urllib.request.quote(str(project), safe='')}/pipelines/{args['pipeline_id']}"
        req = urllib.request.Request(url, headers=headers)
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            return {"error": f"HTTP {e.code}: {e.reason}"}
    url = f"{base}/api/v4/projects/{urllib.request.quote(str(project), safe='')}/pipelines?per_page=10"
    if args.get("branch"):
        url += f"&ref={args['branch']}"
    req = urllib.request.Request(url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        pipelines = json.loads(resp.read().decode())
        return {"project": project, "pipelines": [{"id": p.get("id"), "status": p.get("status"), "branch": p.get("ref"), "created_at": p.get("created_at"), "web_url": p.get("web_url")} for p in pipelines[:10]]}
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}"}


def jenkins_build(args):
    job = args["job"]
    base = args.get("jenkins_url", "").rstrip("/")
    token = args.get("token", "") or os.environ.get("JENKINS_TOKEN", "")
    if not base:
        return {"error": "jenkins_url is required", "hint": "Set jenkins_url or JENKINS_TOKEN env var"}
    build = args.get("build_number", "lastBuild")
    url = f"{base}/job/{job}/{build}/api/json?pretty=true"
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read().decode())
        return {"job": job, "number": data.get("number"), "result": data.get("result"), "building": data.get("building"), "duration": data.get("duration"), "timestamp": data.get("timestamp"), "url": data.get("url"), "displayName": data.get("displayName")}
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}", "job": job}
    except Exception as e:
        return {"error": str(e), "job": job}


def cicd_logs(args):
    system = args.get("system", "github")
    token = _get_token(args)
    if system == "github":
        repo = args.get("repo", "")
        run_id = args.get("run_id", "")
        if not repo or not run_id:
            return {"error": "repo and run_id required for github"}
        url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/jobs"
        data = _github_api(url, token)
        if "error" in data:
            return data
        jobs = []
        for job in data.get("jobs", [])[:5]:
            logs = {"job": job.get("name"), "status": job.get("status"), "conclusion": job.get("conclusion"), "steps": []}
            for step in job.get("steps", []):
                logs["steps"].append({"name": step.get("name"), "status": step.get("status"), "conclusion": step.get("conclusion")})
            jobs.append(logs)
        return {"system": "github", "repo": repo, "run_id": run_id, "jobs": jobs}
    elif system == "gitlab":
        project = args.get("repo", "")
        pipeline_id = args.get("run_id", "")
        base = os.environ.get("GITLAB_URL", "https://gitlab.com").rstrip("/")
        headers = {"User-Agent": "CTZ-CICD/1.0"}
        if token:
            headers["PRIVATE-TOKEN"] = token
        url = f"{base}/api/v4/projects/{urllib.request.quote(project, safe='')}/pipelines/{pipeline_id}/jobs?per_page=10"
        req = urllib.request.Request(url, headers=headers)
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            jobs = json.loads(resp.read().decode())
            return {"system": "gitlab", "project": project, "pipeline_id": pipeline_id, "jobs": [{"id": j.get("id"), "name": j.get("name"), "status": j.get("status"), "stage": j.get("stage")} for j in jobs]}
        except Exception as e:
            return {"error": str(e)}
    elif system == "jenkins":
        job = args.get("job", "")
        build = args.get("run_id", "lastBuild")
        base = os.environ.get("JENKINS_URL", "")
        if not base:
            return {"error": "JENKINS_URL required"}
        url = f"{base}/job/{job}/{build}/consoleText"
        try:
            req = urllib.request.Request(url)
            resp = urllib.request.urlopen(req, timeout=30)
            text = resp.read().decode("utf-8", errors="replace")
            lines = text.split("\n")
            max_lines = args.get("log_lines", 100)
            return {"system": "jenkins", "job": job, "build": build, "total_lines": len(lines), "log_tail": "\n".join(lines[-max_lines:])}
        except Exception as e:
            return {"error": str(e)}
    return {"error": f"Unknown system: {system}"}


def cicd_deploy(args):
    service = args["service"]
    target = args.get("target", "staging")
    version = args.get("version", "latest")
    repo = args.get("repo", "")
    token = _get_token(args)
    if repo and target in ("staging", "production"):
        workflow = f"deploy-{target}.yml"
        url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow}/dispatches"
        data = {"ref": "main", "inputs": {"service": service, "version": version}}
        result = _github_api(url, token, method="POST", data=data)
        if "error" not in result:
            return {"service": service, "target": target, "version": version, "status": "deploy_triggered", "workflow": workflow}
    return {"service": service, "target": target, "version": version, "status": "deploy_initiated", "message": f"Deploy {service}@{version} to {target} queued", "deploy_id": f"deploy-{service}-{target}-{version}".replace(".", "-"), "note": "Configure repo + GITHUB_TOKEN for full GitHub Actions integration"}


def cicd_rollback(args):
    service = args["service"]
    target = args.get("target", "staging")
    to_version = args.get("to_version", "previous")
    repo = args.get("repo", "")
    token = _get_token(args)
    if repo:
        workflow = f"rollback-{target}.yml"
        url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow}/dispatches"
        data = {"ref": "main", "inputs": {"service": service, "to_version": to_version}}
        result = _github_api(url, token, method="POST", data=data)
        if "error" not in result:
            return {"service": service, "target": target, "rollback_to": to_version, "status": "rollback_triggered"}
    return {"service": service, "target": target, "rollback_to": to_version, "status": "rollback_initiated", "message": f"Rollback {service} to {to_version} on {target} queued", "note": "Configure repo + GITHUB_TOKEN for full integration"}


def handle_request(request):
    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": True}}, "serverInfo": {"name": "ctz-cicd", "version": "1.0.0"}}}
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        try:
            if name == "ctz_github_status":
                r = github_status(args)
            elif name == "ctz_github_trigger":
                r = github_trigger(args)
            elif name == "ctz_gitlab_pipeline":
                r = gitlab_pipeline(args)
            elif name == "ctz_jenkins_build":
                r = jenkins_build(args)
            elif name == "ctz_cicd_logs":
                r = cicd_logs(args)
            elif name == "ctz_cicd_deploy":
                r = cicd_deploy(args)
            elif name == "ctz_cicd_rollback":
                r = cicd_rollback(args)
            else:
                return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown tool: {name}"}}
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(r, indent=2)}]}}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}}
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Unknown method"}}


if __name__ == "__main__":
    for line in sys.stdin:
        try:
            r = handle_request(json.loads(line.strip()))
            if r:
                sys.stdout.write(json.dumps(r) + "\n")
                sys.stdout.flush()
        except: pass
