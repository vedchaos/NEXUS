"""CHAOS TYPE ZERO Dashboard Server — serves the web dashboard"""

import http.server
import json
import os
import sys
import platform
import time
import socket
import threading
from urllib.parse import urlparse, parse_qs
from pathlib import Path

PORT = 8080
DASHBOARD_DIR = Path(__file__).parent
NEXUS_DIR = DASHBOARD_DIR.parent
START_TIME = time.time()


class CTZHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler for the CTZ dashboard."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DASHBOARD_DIR), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        routes = {
            '/api/status': self.handle_status,
            '/api/servers': self.handle_servers,
            '/api/memory': self.handle_memory,
            '/api/automations': self.handle_automations,
        }

        if path in routes:
            data = routes[path]()
            self.send_json(data)
        elif path == '/' or path == '/index.html':
            self.path = '/index.html'
            super().do_GET()
        else:
            super().do_GET()

    def send_json(self, data):
        body = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, fmt, *args):
        ts = time.strftime('%H:%M:%S')
        sys.stderr.write(f"\033[90m[{ts}]\033[0m {args[0]}\n")

    def handle_status(self):
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            return {
                'hostname': platform.node(),
                'uptime': self._format_uptime(time.time() - START_TIME),
                'status': 'SYSTEM NOMINAL',
                'cpu': {
                    'percent': round(cpu, 1),
                    'detail': f"{psutil.cpu_count()} cores // {platform.processor() or 'unknown'}",
                },
                'ram': {
                    'percent': round(mem.percent, 1),
                    'detail': f"{round(mem.used / (1024**3), 1)} GB / {round(mem.total / (1024**3), 1)} GB",
                },
                'disk': {
                    'percent': round(disk.percent, 1),
                    'detail': f"{round(disk.used / (1024**3), 1)} GB / {round(disk.total / (1024**3), 1)} GB",
                },
            }
        except ImportError:
            return self._mock_status()

    def handle_servers(self):
        servers = []
        data_dir = NEXUS_DIR / 'data'
        modules = [
            ('bridge_core', 'Core Bridge'),
            ('memory_engine', 'Memory Engine'),
            ('heuristics', 'Heuristics Engine'),
        ]
        for mod_name, display_name in modules:
            mod_path = NEXUS_DIR / f'{mod_name}.py'
            if mod_path.exists():
                servers.append({
                    'name': display_name,
                    'status': 'online',
                    'tools': self._count_tools(mod_path),
                    'uptime': self._format_uptime(time.time() - START_TIME),
                })

        ollama_path = None
        for p in ['/usr/local/bin/ollama', '/usr/bin/ollama',
                   str(Path.home() / 'AppData/Local/Programs/Ollama/ollama.exe')]:
            if os.path.isfile(p):
                ollama_path = p
                break
        if ollama_path:
            servers.append({
                'name': 'Ollama (Local LLM)',
                'status': 'online',
                'tools': 1,
                'uptime': '--',
            })

        if not servers:
            servers = self._mock_servers()

        return servers

    def handle_memory(self):
        data_dir = NEXUS_DIR / 'data'
        ledger_count = self._count_lines(data_dir / 'memory' / 'ledger.jsonl')
        context_count = self._count_lines(data_dir / 'context' / 'sessions.jsonl')
        cache_size = self._dir_size(data_dir / 'cache')

        return {
            'ledger_entries': ledger_count,
            'context_sessions': context_count,
            'cache_hits': self._get_cache_hits(data_dir),
            'cache_size': self._format_size(cache_size),
        }

    def handle_automations(self):
        auto_dir = NEXUS_DIR / 'data' / 'automation'
        automations = []
        if auto_dir.exists():
            for f in sorted(auto_dir.glob('*.json')):
                try:
                    with open(f, 'r', encoding='utf-8') as fp:
                        data = json.load(fp)
                        automations.append({
                            'name': data.get('name', f.stem),
                            'schedule': data.get('schedule', 'unknown'),
                            'active': data.get('active', True),
                        })
                except (json.JSONDecodeError, OSError):
                    continue

        if not automations:
            automations = [
                {'name': 'Memory Consolidation', 'schedule': 'Every 6h', 'active': True},
                {'name': 'Log Rotation', 'schedule': 'Daily 03:00', 'active': True},
                {'name': 'Health Ping', 'schedule': 'Every 5m', 'active': True},
                {'name': 'Backup Vault', 'schedule': 'Daily 04:00', 'active': False},
            ]

        return automations

    def _count_tools(self, path):
        count = 0
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    stripped = line.strip()
                    if stripped.startswith('def ') and not stripped.startswith('def _'):
                        count += 1
        except OSError:
            pass
        return max(count, 1)

    def _count_lines(self, path):
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for _ in f)
        except (OSError, FileNotFoundError):
            return 0

    def _dir_size(self, path):
        total = 0
        if path.exists():
            for f in path.rglob('*'):
                if f.is_file():
                    total += f.stat().st_size
        return total

    def _get_cache_hits(self, data_dir):
        meta = data_dir / 'meta_reasoner' / 'cache_stats.json'
        try:
            with open(meta, 'r', encoding='utf-8') as f:
                return json.load(f).get('hits', 0)
        except (OSError, json.JSONDecodeError, KeyError):
            return 0

    def _format_uptime(self, seconds):
        d = int(seconds // 86400)
        h = int((seconds % 86400) // 3600)
        m = int((seconds % 3600) // 60)
        if d > 0:
            return f"{d}d {h}h {m}m"
        if h > 0:
            return f"{h}h {m}m"
        return f"{m}m"

    def _format_size(self, size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def _mock_status(self):
        return {
            'hostname': platform.node(),
            'uptime': self._format_uptime(time.time() - START_TIME),
            'status': 'SYSTEM NOMINAL',
            'cpu': {'percent': 23, 'detail': 'psutil not installed'},
            'ram': {'percent': 61, 'detail': 'Install psutil for real data'},
            'disk': {'percent': 44, 'detail': 'Install psutil for real data'},
        }

    def _mock_servers(self):
        return [
            {'name': 'CTZ Core', 'status': 'online', 'tools': 6, 'uptime': self._format_uptime(time.time() - START_TIME)},
            {'name': 'Memory Engine', 'status': 'online', 'tools': 4, 'uptime': self._format_uptime(time.time() - START_TIME)},
            {'name': 'Heuristics', 'status': 'online', 'tools': 2, 'uptime': self._format_uptime(time.time() - START_TIME)},
        ]


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT

    try:
        server = http.server.HTTPServer(('0.0.0.0', port), CTZHandler)
    except OSError as e:
        print(f"\033[91m[ERROR]\033[0m Port {port} unavailable: {e}")
        sys.exit(1)

    print(f"""
\033[92m  ╔══════════════════════════════════════╗
  ║  CHAOS TYPE ZERO — Dashboard Server  ║
  ║  Port : {port:<28}║
  ║  URL  : http://localhost:{port:<13}║
  ║  Time : {time.strftime('%Y-%m-%d %H:%M:%S'):<28}║
  ╚══════════════════════════════════════╝\033[0m
  Press Ctrl+C to stop.
""")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\033[93m[SHUTDOWN]\033[0m Dashboard server stopped.")
        server.server_close()


if __name__ == '__main__':
    main()
