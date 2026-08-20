#!/usr/bin/env python3
"""CHAOS TYPE ZERO MCP — Communication Server"""

import json
import sys
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent / "data" / "comms"
CONFIG_PATH = DATA_DIR / "config.json"
DB_PATH = DATA_DIR / "history.db"


def ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_config():
    ensure_dirs()
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return {}


def save_config(cfg):
    ensure_dirs()
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))


def get_db():
    ensure_dirs()
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT NOT NULL,
        channel TEXT NOT NULL,
        direction TEXT NOT NULL,
        recipient TEXT,
        subject TEXT,
        body TEXT,
        status TEXT,
        meta TEXT
    )""")
    conn.commit()
    return conn


def log_comms(channel, direction, recipient, subject, body, status, meta=None):
    db = get_db()
    db.execute(
        "INSERT INTO history (ts, channel, direction, recipient, subject, body, status, meta) VALUES (?,?,?,?,?,?,?,?)",
        (datetime.utcnow().isoformat(), channel, direction, recipient, subject, body, status, json.dumps(meta) if meta else None),
    )
    db.commit()
    db.close()


TOOLS = [
    {
        "name": "ctz_email_send",
        "description": "Send email via SMTP",
        "inputSchema": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email"},
                "subject": {"type": "string", "default": ""},
                "body": {"type": "string", "default": ""},
                "html": {"type": "string", "default": ""},
                "cc": {"type": "string", "default": ""},
                "bcc": {"type": "string", "default": ""},
            },
            "required": ["to"],
        },
    },
    {
        "name": "ctz_email_read",
        "description": "Read a specific email by UID from IMAP",
        "inputSchema": {
            "type": "object",
            "properties": {
                "uid": {"type": "string", "description": "Email UID"},
                "folder": {"type": "string", "default": "INBOX"},
            },
            "required": ["uid"],
        },
    },
    {
        "name": "ctz_email_list",
        "description": "List recent emails from IMAP",
        "inputSchema": {
            "type": "object",
            "properties": {
                "folder": {"type": "string", "default": "INBOX"},
                "limit": {"type": "integer", "default": 10},
                "search": {"type": "string", "default": "ALL", "description": "IMAP search filter (e.g. UNSEEN)"},
            },
        },
    },
    {
        "name": "ctz_slack_send",
        "description": "Send Slack message via webhook",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Message text"},
                "channel": {"type": "string", "default": "", "description": "Override channel (if webhook allows)"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "ctz_discord_send",
        "description": "Send Discord message via webhook",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Message content"},
                "username": {"type": "string", "default": "CTZ Bot"},
            },
            "required": ["content"],
        },
    },
    {
        "name": "ctz_webhook_send",
        "description": "Send generic webhook POST with JSON body",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Webhook URL"},
                "data": {"type": "object", "description": "JSON payload"},
                "headers": {"type": "object", "description": "Extra HTTP headers"},
            },
            "required": ["url", "data"],
        },
    },
    {
        "name": "ctz_telegram_send",
        "description": "Send Telegram message via Bot API",
        "inputSchema": {
            "type": "object",
            "properties": {
                "chat_id": {"type": "string", "description": "Chat ID or @channel"},
                "text": {"type": "string", "description": "Message text"},
                "parse_mode": {"type": "string", "default": "", "description": "Markdown or HTML"},
            },
            "required": ["chat_id", "text"],
        },
    },
    {
        "name": "ctz_comms_log",
        "description": "Log a communication event to history database",
        "inputSchema": {
            "type": "object",
            "properties": {
                "channel": {"type": "string", "description": "Channel name (email, slack, discord, etc.)"},
                "direction": {"type": "string", "enum": ["outbound", "inbound"], "default": "outbound"},
                "recipient": {"type": "string", "default": ""},
                "subject": {"type": "string", "default": ""},
                "body": {"type": "string", "default": ""},
                "status": {"type": "string", "default": "sent"},
            },
            "required": ["channel"],
        },
    },
    {
        "name": "ctz_comms_history",
        "description": "Query communication history",
        "inputSchema": {
            "type": "object",
            "properties": {
                "channel": {"type": "string", "default": ""},
                "direction": {"type": "string", "default": ""},
                "limit": {"type": "integer", "default": 20},
                "since": {"type": "string", "default": "", "description": "ISO date filter"},
            },
        },
    },
]


def handle_request(request):
    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": True}},
                "serverInfo": {"name": "ctz-comms", "version": "1.0.0"},
            },
        }

    if method == "notifications/initialized":
        return None

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}

    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        try:
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(call_tool(name, args))}]}}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}}

    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Unknown method"}}


def call_tool(name, args):
    cfg = load_config()

    if name == "ctz_email_send":
        return _email_send(cfg, args)
    elif name == "ctz_email_read":
        return _email_read(cfg, args)
    elif name == "ctz_email_list":
        return _email_list(cfg, args)
    elif name == "ctz_slack_send":
        return _slack_send(cfg, args)
    elif name == "ctz_discord_send":
        return _discord_send(cfg, args)
    elif name == "ctz_webhook_send":
        return _webhook_send(cfg, args)
    elif name == "ctz_telegram_send":
        return _telegram_send(cfg, args)
    elif name == "ctz_comms_log":
        return _comms_log(args)
    elif name == "ctz_comms_history":
        return _comms_history(args)
    return {"error": "Unknown tool"}


# ── Email ──────────────────────────────────────────────────────────────────

def _email_send(cfg, args):
    smtp_cfg = cfg.get("smtp", {})
    if not smtp_cfg.get("host"):
        return {"status": "error", "message": "SMTP not configured. Set smtp.host, smtp.port, smtp.user, smtp.pass in data/comms/config.json"}

    msg = MIMEMultipart("alternative" if args.get("html") else "plain")
    msg["From"] = smtp_cfg.get("from", smtp_cfg.get("user", ""))
    msg["To"] = args["to"]
    if args.get("subject"):
        msg["Subject"] = args["subject"]
    if args.get("cc"):
        msg["Cc"] = args["cc"]

    if args.get("html"):
        msg.attach(MIMEText(args.get("body", ""), "plain"))
        msg.attach(MIMEText(args["html"], "html"))
    else:
        msg.attach(MIMEText(args.get("body", ""), "plain"))

    recipients = [args["to"]]
    if args.get("cc"):
        recipients.extend(args["cc"].split(","))
    if args.get("bcc"):
        recipients.extend(args["bcc"].split(","))

    port = int(smtp_cfg.get("port", 587))
    use_tls = smtp_cfg.get("tls", True)

    with smtplib.SMTP(smtp_cfg["host"], port, timeout=30) as server:
        if use_tls:
            server.starttls()
        if smtp_cfg.get("user") and smtp_cfg.get("pass"):
            server.login(smtp_cfg["user"], smtp_cfg["pass"])
        server.sendmail(msg["From"], recipients, msg.as_string())

    log_comms("email", "outbound", args["to"], args.get("subject", ""), args.get("body", ""), "sent")
    return {"status": "sent", "to": args["to"], "subject": args.get("subject", "")}


def _imap_connect(cfg):
    imap_cfg = cfg.get("imap", {})
    if not imap_cfg.get("host"):
        raise RuntimeError("IMAP not configured. Set imap.host, imap.port, imap.user, imap.pass in data/comms/config.json")
    port = int(imap_cfg.get("port", 993))
    ssl = imap_cfg.get("ssl", True)
    if ssl:
        mail = imaplib.IMAP4_SSL(imap_cfg["host"], port)
    else:
        mail = imaplib.IMAP4(imap_cfg["host"], port)
    mail.login(imap_cfg["user"], imap_cfg["pass"])
    return mail


def _email_read(cfg, args):
    mail = _imap_connect(cfg)
    folder = args.get("folder", "INBOX")
    mail.select(folder)
    status, data = mail.uid("fetch", args["uid"], "(RFC822)")
    if status != "OK":
        mail.logout()
        return {"error": f"UID {args['uid']} not found"}
    raw = data[0][1]
    msg = email.message_from_bytes(raw)
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == "text/plain" and not part.get("Content-Disposition", "").startswith("attachment"):
                body = part.get_payload(decode=True).decode(errors="replace")
                break
    else:
        body = msg.get_payload(decode=True).decode(errors="replace")
    mail.logout()
    result = {
        "uid": args["uid"],
        "from": msg.get("From", ""),
        "to": msg.get("To", ""),
        "subject": msg.get("Subject", ""),
        "date": msg.get("Date", ""),
        "body": body,
    }
    log_comms("email", "inbound", msg.get("From", ""), msg.get("Subject", ""), body, "read", {"uid": args["uid"]})
    return result


def _email_list(cfg, args):
    mail = _imap_connect(cfg)
    folder = args.get("folder", "INBOX")
    mail.select(folder)
    search_filter = args.get("search", "ALL")
    status, msg_ids = mail.search(None, search_filter)
    if status != "OK":
        mail.logout()
        return {"error": "Search failed"}
    ids = msg_ids[0].split()
    limit = args.get("limit", 10)
    ids = ids[-limit:]
    results = []
    for uid in reversed(ids):
        status, data = mail.uid("fetch", uid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
        if status == "OK" and data[0]:
            header_bytes = data[0][1]
            hdr = email.message_from_bytes(header_bytes)
            results.append({
                "uid": uid.decode(),
                "from": hdr.get("From", ""),
                "subject": hdr.get("Subject", ""),
                "date": hdr.get("Date", ""),
            })
    mail.logout()
    return {"count": len(results), "emails": results}


# ── Webhooks ───────────────────────────────────────────────────────────────

def _post_json(url, payload, extra_headers=None):
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return {"status": resp.status, "body": resp.read().decode(errors="replace")}


def _slack_send(cfg, args):
    webhook = cfg.get("slack_webhook", "")
    if not webhook:
        return {"status": "error", "message": "Slack webhook not configured. Set slack_webhook in data/comms/config.json"}
    payload = {"text": args["text"]}
    if args.get("channel"):
        payload["channel"] = args["channel"]
    result = _post_json(webhook, payload)
    log_comms("slack", "outbound", args.get("channel", ""), "", args["text"], "sent")
    return {"status": "sent", "channel": args.get("channel", ""), "response": result}


def _discord_send(cfg, args):
    webhook = cfg.get("discord_webhook", "")
    if not webhook:
        return {"status": "error", "message": "Discord webhook not configured. Set discord_webhook in data/comms/config.json"}
    payload = {"content": args["content"]}
    if args.get("username"):
        payload["username"] = args["username"]
    result = _post_json(webhook, payload)
    log_comms("discord", "outbound", "", "", args["content"], "sent")
    return {"status": "sent", "response": result}


def _webhook_send(cfg, args):
    headers = args.get("headers", {})
    result = _post_json(args["url"], args["data"], headers)
    log_comms("webhook", "outbound", args["url"], "", json.dumps(args["data"]), "sent")
    return {"status": "sent", "url": args["url"], "response": result}


def _telegram_send(cfg, args):
    token = cfg.get("telegram_token", "")
    if not token:
        return {"status": "error", "message": "Telegram token not configured. Set telegram_token in data/comms/config.json"}
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": args["chat_id"], "text": args["text"]}
    if args.get("parse_mode"):
        payload["parse_mode"] = args["parse_mode"]
    result = _post_json(url, payload)
    log_comms("telegram", "outbound", args["chat_id"], "", args["text"], "sent")
    return {"status": "sent", "chat_id": args["chat_id"], "response": result}


# ── Comms History ──────────────────────────────────────────────────────────

def _comms_log(args):
    log_comms(
        channel=args["channel"],
        direction=args.get("direction", "outbound"),
        recipient=args.get("recipient", ""),
        subject=args.get("subject", ""),
        body=args.get("body", ""),
        status=args.get("status", "sent"),
    )
    return {"status": "logged", "channel": args["channel"]}


def _comms_history(args):
    db = get_db()
    query = "SELECT id, ts, channel, direction, recipient, subject, body, status FROM history WHERE 1=1"
    params = []
    if args.get("channel"):
        query += " AND channel = ?"
        params.append(args["channel"])
    if args.get("direction"):
        query += " AND direction = ?"
        params.append(args["direction"])
    if args.get("since"):
        query += " AND ts >= ?"
        params.append(args["since"])
    query += " ORDER BY id DESC LIMIT ?"
    params.append(args.get("limit", 20))
    rows = db.execute(query, params).fetchall()
    db.close()
    results = [{"id": r[0], "ts": r[1], "channel": r[2], "direction": r[3], "recipient": r[4], "subject": r[5], "body": r[6], "status": r[7]} for r in rows]
    return {"count": len(results), "history": results}


if __name__ == "__main__":
    for line in sys.stdin:
        try:
            r = handle_request(json.loads(line.strip()))
            if r:
                sys.stdout.write(json.dumps(r) + "\n")
                sys.stdout.flush()
        except:
            pass
