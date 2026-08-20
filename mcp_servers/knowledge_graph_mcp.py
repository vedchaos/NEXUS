#!/usr/bin/env python3
"""CHAOS TYPE ZERO MCP — Knowledge Graph Server"""

import json
import sys
import sqlite3
import uuid
import time
from collections import defaultdict, deque
from pathlib import Path

DB_DIR = Path(__file__).parent.parent / "data" / "knowledge"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "graph.db"

TOOLS = [
    {"name": "ctz_kg_add_entity", "description": "Add entity (person, concept, place, event, etc.) to knowledge graph", "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}, "entity_type": {"type": "string", "default": "concept"}, "attributes": {"type": "object", "default": {}}, "description": {"type": "string", "default": ""}}, "required": ["name"]}},
    {"name": "ctz_kg_add_relation", "description": "Add directed relation between two entities", "inputSchema": {"type": "object", "properties": {"source": {"type": "string"}, "target": {"type": "string"}, "relation_type": {"type": "string"}, "weight": {"type": "number", "default": 1.0}, "attributes": {"type": "object", "default": {}}}, "required": ["source", "target", "relation_type"]}},
    {"name": "ctz_kg_query", "description": "Query knowledge graph by entity name, type, or relation pattern", "inputSchema": {"type": "object", "properties": {"entity_name": {"type": "string", "default": ""}, "entity_type": {"type": "string", "default": ""}, "relation_type": {"type": "string", "default": ""}, "limit": {"type": "integer", "default": 50}}}},
    {"name": "ctz_kg_path", "description": "Find shortest path between two entities", "inputSchema": {"type": "object", "properties": {"source": {"type": "string"}, "target": {"type": "string"}, "max_depth": {"type": "integer", "default": 6}}, "required": ["source", "target"]}},
    {"name": "ctz_kg_neighbors", "description": "Get neighbors of an entity (incoming and outgoing relations)", "inputSchema": {"type": "object", "properties": {"entity_name": {"type": "string"}, "depth": {"type": "integer", "default": 1}, "relation_filter": {"type": "string", "default": ""}}, "required": ["entity_name"]}},
    {"name": "ctz_kg_export", "description": "Export entire knowledge graph as JSON", "inputSchema": {"type": "object", "properties": {"format": {"type": "string", "default": "json"}}}},
    {"name": "ctz_kg_import", "description": "Import knowledge graph from JSON format", "inputSchema": {"type": "object", "properties": {"data": {"type": "string"}, "format": {"type": "string", "default": "json"}}, "required": ["data"]}},
    {"name": "ctz_kg_stats", "description": "Knowledge graph statistics (entity count, relation count, density, types)", "inputSchema": {"type": "object", "properties": {}}},
]


def _get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _init_db(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS entities (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            entity_type TEXT NOT NULL DEFAULT 'concept',
            description TEXT DEFAULT '',
            attributes TEXT DEFAULT '{}',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
        CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);

        CREATE TABLE IF NOT EXISTS relations (
            id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            target_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            weight REAL DEFAULT 1.0,
            attributes TEXT DEFAULT '{}',
            created_at REAL NOT NULL,
            FOREIGN KEY (source_id) REFERENCES entities(id) ON DELETE CASCADE,
            FOREIGN KEY (target_id) REFERENCES entities(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_id);
        CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target_id);
        CREATE INDEX IF NOT EXISTS idx_relations_type ON relations(relation_type);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_relations_unique ON relations(source_id, target_id, relation_type);
    """)
    conn.commit()


def _entity_to_dict(row):
    return {"id": row["id"], "name": row["name"], "type": row["entity_type"], "description": row["description"], "attributes": json.loads(row["attributes"]), "created_at": row["created_at"]}


def _relation_to_dict(row, conn):
    src = conn.execute("SELECT name FROM entities WHERE id=?", (row["source_id"],)).fetchone()
    tgt = conn.execute("SELECT name FROM entities WHERE id=?", (row["target_id"],)).fetchone()
    return {"id": row["id"], "source": src["name"] if src else "?", "target": tgt["name"] if tgt else "?", "relation_type": row["relation_type"], "weight": row["weight"], "attributes": json.loads(row["attributes"])}


def handle_request(request):
    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": True}}, "serverInfo": {"name": "ctz-knowledge-graph", "version": "1.0.0"}}}
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        conn = _get_db()
        _init_db(conn)
        try:
            if name == "ctz_kg_add_entity":
                now = time.time()
                eid = str(uuid.uuid4())[:12]
                attrs = json.dumps(args.get("attributes", {}))
                try:
                    conn.execute("INSERT INTO entities (id, name, entity_type, description, attributes, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
                                 (eid, args["name"], args.get("entity_type", "concept"), args.get("description", ""), attrs, now, now))
                    conn.commit()
                    return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"status": "created", "id": eid, "name": args["name"], "type": args.get("entity_type", "concept")})}]}}
                except sqlite3.IntegrityError:
                    row = conn.execute("SELECT * FROM entities WHERE name=?", (args["name"],)).fetchone()
                    if row:
                        conn.execute("UPDATE entities SET description=?, attributes=?, updated_at=? WHERE id=?",
                                     (args.get("description", row["description"]), attrs, now, row["id"]))
                        conn.commit()
                        return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"status": "updated", "id": row["id"], "name": args["name"]})}]}}
                    raise

            elif name == "ctz_kg_add_relation":
                src = conn.execute("SELECT id FROM entities WHERE name=?", (args["source"],)).fetchone()
                tgt = conn.execute("SELECT id FROM entities WHERE name=?", (args["target"],)).fetchone()
                if not src:
                    return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"error": f"Source entity not found: {args['source']}"})}], "isError": True}}
                if not tgt:
                    return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"error": f"Target entity not found: {args['target']}"})}], "isError": True}}
                rid = str(uuid.uuid4())[:12]
                attrs = json.dumps(args.get("attributes", {}))
                try:
                    conn.execute("INSERT INTO relations (id, source_id, target_id, relation_type, weight, attributes, created_at) VALUES (?,?,?,?,?,?,?)",
                                 (rid, src["id"], tgt["id"], args["relation_type"], args.get("weight", 1.0), attrs, time.time()))
                    conn.commit()
                    return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"status": "created", "id": rid, "source": args["source"], "target": args["target"], "relation_type": args["relation_type"]})}]}}
                except sqlite3.IntegrityError:
                    return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"status": "exists", "source": args["source"], "target": args["target"], "relation_type": args["relation_type"]})}]}}

            elif name == "ctz_kg_query":
                limit = args.get("limit", 50)
                if args.get("entity_name"):
                    rows = conn.execute("SELECT * FROM entities WHERE name LIKE ? LIMIT ?", (f"%{args['entity_name']}%", limit)).fetchall()
                    results = {"entities": [_entity_to_dict(r) for r in rows]}
                    if rows:
                        eids = [r["id"] for r in rows]
                        placeholders = ",".join("?" * len(eids))
                        rels = conn.execute(f"SELECT * FROM relations WHERE source_id IN ({placeholders}) OR target_id IN ({placeholders})", eids + eids).fetchall()
                        results["relations"] = [_relation_to_dict(r, conn) for r in rels]
                    else:
                        results["relations"] = []
                    return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(results, indent=2)}]}}
                elif args.get("entity_type"):
                    rows = conn.execute("SELECT * FROM entities WHERE entity_type=? LIMIT ?", (args["entity_type"], limit)).fetchall()
                    return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"entities": [_entity_to_dict(r) for r in rows]}, indent=2)}]}}
                elif args.get("relation_type"):
                    rows = conn.execute("SELECT * FROM relations WHERE relation_type=? LIMIT ?", (args["relation_type"], limit)).fetchall()
                    return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"relations": [_relation_to_dict(r, conn) for r in rows]}, indent=2)}]}}
                else:
                    entities = conn.execute("SELECT * FROM entities LIMIT ?", (limit,)).fetchall()
                    return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"entities": [_entity_to_dict(r) for r in entities]}, indent=2)}]}}

            elif name == "ctz_kg_path":
                src_row = conn.execute("SELECT id FROM entities WHERE name=?", (args["source"],)).fetchone()
                tgt_row = conn.execute("SELECT id FROM entities WHERE name=?", (args["target"],)).fetchone()
                if not src_row or not tgt_row:
                    return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"error": "Source or target entity not found"})}], "isError": True}}
                max_depth = args.get("max_depth", 6)
                adj = defaultdict(list)
                for rel in conn.execute("SELECT source_id, target_id, relation_type FROM relations"):
                    adj[rel["source_id"]].append((rel["target_id"], rel["relation_type"]))
                    adj[rel["target_id"]].append((rel["source_id"], rel["relation_type"]))
                visited = {src_row["id"]: None}
                queue = deque([(src_row["id"], [])])
                found_path = None
                while queue and not found_path:
                    current, path = queue.popleft()
                    if current == tgt_row["id"]:
                        found_path = path
                        break
                    if len(path) >= max_depth:
                        continue
                    for neighbor, rel_type in adj.get(current, []):
                        if neighbor not in visited:
                            visited[neighbor] = current
                            queue.append((neighbor, path + [{"from": current, "to": neighbor, "via": rel_type}]))
                if found_path:
                    entity_ids = [src_row["id"]] + [step["to"] for step in found_path]
                    placeholders = ",".join("?" * len(entity_ids))
                    rows = conn.execute(f"SELECT id, name, entity_type FROM entities WHERE id IN ({placeholders})", entity_ids).fetchall()
                    name_map = {r["id"]: {"name": r["name"], "type": r["entity_type"]} for r in rows}
                    path_names = [{"name": name_map.get(eid, {}).get("name", eid), "type": name_map.get(eid, {}).get("type", "?"), "via": step["via"]} for eid, step in zip(entity_ids, [{"via": "start"}] + found_path)]
                    return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"found": True, "length": len(found_path), "path": path_names})}]}}
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"found": False, "note": f"No path found within depth {max_depth}"})}]}}

            elif name == "ctz_kg_neighbors":
                entity_row = conn.execute("SELECT id FROM entities WHERE name=?", (args["entity_name"],)).fetchone()
                if not entity_row:
                    return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"error": f"Entity not found: {args['entity_name']}"})}], "isError": True}}
                depth = args.get("depth", 1)
                rel_filter = args.get("relation_filter", "")
                neighbors = {"outgoing": [], "incoming": []}
                if rel_filter:
                    out_rels = conn.execute("SELECT r.*, e.name as target_name, e.entity_type as target_type FROM relations r JOIN entities e ON r.target_id=e.id WHERE r.source_id=? AND r.relation_type=?", (entity_row["id"], rel_filter)).fetchall()
                    in_rels = conn.execute("SELECT r.*, e.name as source_name, e.entity_type as source_type FROM relations r JOIN entities e ON r.source_id=e.id WHERE r.target_id=? AND r.relation_type=?", (entity_row["id"], rel_filter)).fetchall()
                else:
                    out_rels = conn.execute("SELECT r.*, e.name as target_name, e.entity_type as target_type FROM relations r JOIN entities e ON r.target_id=e.id WHERE r.source_id=?", (entity_row["id"],)).fetchall()
                    in_rels = conn.execute("SELECT r.*, e.name as source_name, e.entity_type as source_type FROM relations r JOIN entities e ON r.source_id=e.id WHERE r.target_id=?", (entity_row["id"],)).fetchall()
                for r in out_rels:
                    neighbors["outgoing"].append({"target": r["target_name"], "target_type": r["target_type"], "relation_type": r["relation_type"], "weight": r["weight"]})
                for r in in_rels:
                    neighbors["incoming"].append({"source": r["source_name"], "source_type": r["source_type"], "relation_type": r["relation_type"], "weight": r["weight"]})
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(neighbors, indent=2)}]}}

            elif name == "ctz_kg_export":
                entities = [_entity_to_dict(r) for r in conn.execute("SELECT * FROM entities").fetchall()]
                relations = [_relation_to_dict(r, conn) for r in conn.execute("SELECT * FROM relations").fetchall()]
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"entities": entities, "relations": relations}, indent=2)}]}}

            elif name == "ctz_kg_import":
                data = json.loads(args["data"])
                imported = {"entities": 0, "relations": 0, "skipped": 0}
                now = time.time()
                for ent in data.get("entities", []):
                    try:
                        eid = ent.get("id", str(uuid.uuid4())[:12])
                        conn.execute("INSERT OR IGNORE INTO entities (id, name, entity_type, description, attributes, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
                                     (eid, ent["name"], ent.get("type", ent.get("entity_type", "concept")), ent.get("description", ""), json.dumps(ent.get("attributes", {})), ent.get("created_at", now), now))
                        imported["entities"] += 1
                    except Exception:
                        imported["skipped"] += 1
                conn.commit()
                for rel in data.get("relations", []):
                    try:
                        src = conn.execute("SELECT id FROM entities WHERE name=?", (rel["source"],)).fetchone()
                        tgt = conn.execute("SELECT id FROM entities WHERE name=?", (rel["target"],)).fetchone()
                        if src and tgt:
                            rid = rel.get("id", str(uuid.uuid4())[:12])
                            conn.execute("INSERT OR IGNORE INTO relations (id, source_id, target_id, relation_type, weight, attributes, created_at) VALUES (?,?,?,?,?,?,?)",
                                         (rid, src["id"], tgt["id"], rel.get("relation_type", "related"), rel.get("weight", 1.0), json.dumps(rel.get("attributes", {})), rel.get("created_at", now)))
                            imported["relations"] += 1
                    except Exception:
                        imported["skipped"] += 1
                conn.commit()
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"status": "imported", **imported})}]}}

            elif name == "ctz_kg_stats":
                e_count = conn.execute("SELECT COUNT(*) as c FROM entities").fetchone()["c"]
                r_count = conn.execute("SELECT COUNT(*) as c FROM relations").fetchone()["c"]
                type_counts = {r["entity_type"]: r["c"] for r in conn.execute("SELECT entity_type, COUNT(*) as c FROM entities GROUP BY entity_type").fetchall()}
                rel_counts = {r["relation_type"]: r["c"] for r in conn.execute("SELECT relation_type, COUNT(*) as c FROM relations GROUP BY relation_type").fetchall()}
                density = r_count / (e_count * (e_count - 1)) if e_count > 1 else 0.0
                most_connected = None
                if e_count > 0:
                    top = conn.execute("""
                        SELECT e.name, COUNT(r.id) as connections
                        FROM entities e
                        LEFT JOIN relations r ON e.id=r.source_id OR e.id=r.target_id
                        GROUP BY e.id ORDER BY connections DESC LIMIT 1
                    """).fetchone()
                    if top:
                        most_connected = {"name": top["name"], "connections": top["connections"]}
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps({"entities": e_count, "relations": r_count, "density": round(density, 6), "entity_types": type_counts, "relation_types": rel_counts, "most_connected": most_connected}, indent=2)}]}}

        except Exception as e:
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}}
        finally:
            conn.close()
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Unknown method"}}


if __name__ == "__main__":
    for line in sys.stdin:
        try:
            r = handle_request(json.loads(line.strip()))
            if r:
                sys.stdout.write(json.dumps(r) + "\n")
                sys.stdout.flush()
        except: pass
