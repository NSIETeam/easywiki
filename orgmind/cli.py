#!/usr/bin/env python3
"""
EasyWiki CLI — Onboarding & Lifecycle Manager

Usage:
    easywiki start              # Start server (auto-install deps if missing)
    easywiki status             # Check server + agent connections
    easywiki connect <agent>    # Connect an AI agent (auto-detect, auto-config)
    easywiki connect --auto     # Auto-detect and connect all available agents
    easywiki stop               # Stop server
    easywiki logs               # Tail server logs
"""
import os
import sys
import json
import time
import signal
import subprocess
import socket
import shutil
import textwrap
from pathlib import Path

# Resolve project root (works whether installed via pip or run from source)
_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent
_FRONTEND_DIST = _PROJECT_ROOT / "frontend-src" / "dist"

# ── Helpers ──────────────────────────────────────────────────────────────────

def _print_ok(msg):
    print(f"  \033[32m✓\033[0m {msg}")

def _print_err(msg):
    print(f"  \033[31m✗\033[0m {msg}")

def _print_info(msg):
    print(f"  \033[36m→\033[0m {msg}")

def _print_warn(msg):
    print(f"  \033[33m!\033[0m {msg}")

def _print_header(title):
    print(f"\n\033[1m{'='*50}\033[0m")
    print(f"\033[1m {title}\033[0m")
    print(f"\033[1m{'='*50}\033[0m\n")

def _is_port_open(port=8080, host="127.0.0.1"):
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except (OSError, ConnectionRefusedError):
        return False

def _get_easywiki_dir():
    return Path(os.getenv("ORGMIND_DB_PATH", os.path.expanduser("~/.easywiki"))).parent

def _server_pid_file():
    return _get_easywiki_dir() / ".server.pid"

def _log_file():
    return _get_easywiki_dir() / "server.log"

def _ensure_dir():
    d = _get_easywiki_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d

def _check_python():
    """Ensure Python 3.10+"""
    if sys.version_info < (3, 10):
        _print_err(f"Python 3.10+ required, got {sys.version}")
        sys.exit(1)

def _check_deps():
    """Check if core dependencies are installed, offer to install if missing."""
    missing = []
    try:
        import fastapi
    except ImportError:
        missing.append("fastapi")
    try:
        import uvicorn
    except ImportError:
        missing.append("uvicorn")
    try:
        import bcrypt
    except ImportError:
        missing.append("bcrypt")

    if missing:
        _print_warn(f"Missing dependencies: {', '.join(missing)}")
        answer = input("  Install now? [Y/n] ").strip().lower()
        if answer != "n":
            _print_info("Installing dependencies...")
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
            _print_ok("Dependencies installed")
        else:
            _print_err("Cannot start without dependencies. Run: pip install -r requirements.txt")
            sys.exit(1)

def _get_admin_password():
    """Read admin password from bootstrap file or DB."""
    ew_dir = _get_easywiki_dir()
    bootstrap = ew_dir / ".bootstrap_admin"
    if bootstrap.exists():
        content = bootstrap.read_text()
        for line in content.splitlines():
            if line.startswith("Password:"):
                return line.split(":", 1)[1].strip()
    # If bootstrap was cleaned (already logged in), prompt to reset
    return None


# ── Commands ─────────────────────────────────────────────────────────────────

def cmd_start(host="0.0.0.0", port=8080):
    """Start EasyWiki server."""
    _print_header("EasyWiki Server")
    _check_python()
    _check_deps()

    if _is_port_open(port):
        _print_warn(f"Port {port} is already in use. EasyWiki may already be running.")
        answer = input("  Restart? [y/N] ").strip().lower()
        if answer == "y":
            cmd_stop()
        else:
            _print_info(f"Open http://127.0.0.1:{port} in your browser")
            return

    _ensure_dir()
    log_path = _log_file()

    # Start server
    _print_info(f"Starting server on port {port}...")
    env = os.environ.copy()
    env["ORGMIND_DB_PATH"] = str(_get_easywiki_dir() / "easywiki.db")

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "orgmind.main_sqlite:app",
         "--host", host, "--port", str(port)],
        cwd=str(_PROJECT_ROOT),
        env=env,
        stdout=open(log_path, "w"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )

    # Save PID
    _server_pid_file().write_text(str(proc.pid))

    # Wait for server to be ready
    for i in range(30):
        time.sleep(1)
        if _is_port_open(port):
            break
    else:
        _print_err("Server failed to start. Check logs:")
        print(f"  {log_path}")
        sys.exit(1)

    _print_ok(f"Server running at http://127.0.0.1:{port}")

    # Show login info
    password = _get_admin_password()
    if password:
        _print_info(f"Login: admin@local / {password}")
        _print_info("(This password will be removed after first login for security)")
    else:
        _print_info("Login: admin@local / (password already set — use 'easywiki reset-password' if forgotten)")

    print()
    _print_info("Next steps:")
    print("  1. Open the URL above in your browser")
    print("  2. Run: easywiki connect --auto")
    print()

    # Launch browser if possible
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", f"http://127.0.0.1:{port}"])
        elif sys.platform.startswith("linux"):
            subprocess.Popen(["xdg-open", f"http://127.0.0.1:{port}"])
    except Exception:
        pass


def cmd_stop():
    """Stop EasyWiki server."""
    pid_file = _server_pid_file()
    if not pid_file.exists():
        _print_warn("No PID file found. Trying to kill by port...")
        import signal as sig
        try:
            # Try fuser/lsof
            result = subprocess.run(["lsof", "-ti:8080"], capture_output=True, text=True)
            for pid in result.stdout.strip().split("\n"):
                if pid:
                    os.kill(int(pid), sig.SIGTERM)
                    _print_ok(f"Killed process {pid}")
        except Exception:
            _print_err("Could not find or kill server process")
        return

    pid = int(pid_file.read_text().strip())
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(2)
        _print_ok(f"Server stopped (PID {pid})")
    except ProcessLookupError:
        _print_warn(f"Process {pid} not running (stale PID file)")
    finally:
        pid_file.unlink(missing_ok=True)


def cmd_status():
    """Show server status, agent connections, and knowledge stats."""
    _print_header("EasyWiki Status")

    # Server
    if _is_port_open():
        _print_ok("Server: running (http://127.0.0.1:8080)")
    else:
        _print_err("Server: stopped")
        print("  Run: easywiki start")

    # Agent connections
    print()
    from orgmind.connector import AgentConnector
    connector = AgentConnector()
    agents = connector.detect_all_agents()

    if agents:
        _print_ok("Agents detected:")
        for a in agents:
            status = "connected" if a.get("connected") else "detected"
            _print_info(f"{a['name']} ({a['type']}) — {status}")
    else:
        _print_warn("No agents connected")
        print("  Run: easywiki connect --auto")

    # Knowledge stats
    if _is_port_open():
        print()
        try:
            import urllib.request
            resp = urllib.request.urlopen("http://127.0.0.1:8080/api/v1/memories/recent",
                                          data=json.dumps({"limit": 1}).encode(),
                                          headers={"Content-Type": "application/json"})
            data = json.loads(resp.read())
            total = data.get("total", 0)
            if total > 0:
                _print_ok(f"Knowledge base: {total} memories")
            else:
                _print_warn("Knowledge base: empty (start using your agent — knowledge accumulates automatically)")
        except Exception:
            pass


def cmd_connect(agent_name=None, auto=False):
    """Connect an AI agent to EasyWiki."""
    _print_header("Connect Agent")

    from orgmind.connector import AgentConnector
    connector = AgentConnector()

    if auto:
        _print_info("Auto-detecting installed agents...")
        agents = connector.detect_all_agents()
        if not agents:
            _print_err("No agents detected. Install Claude Code, Codex, or other MCP-compatible agents first.")
            return

        for agent in agents:
            _print_info(f"Connecting {agent['name']}...")
            result = connector.connect(agent["type"])
            if result["success"]:
                _print_ok(f"{agent['name']}: {result['message']}")
            else:
                _print_err(f"{agent['name']}: {result['message']}")
    else:
        if not agent_name:
            # Interactive selection
            agents = connector.detect_all_agents()
            if not agents:
                _print_err("No agents detected.")
                return
            print("  Detected agents:")
            for i, a in enumerate(agents, 1):
                print(f"    {i}. {a['name']} ({a['type']})")
            print(f"    0. Cancel")
            choice = input("\n  Select agent: ").strip()
            try:
                idx = int(choice)
                if idx == 0:
                    return
                agent_name = agents[idx - 1]["type"]
            except (ValueError, IndexError):
                _print_err("Invalid selection")
                return

        _print_info(f"Connecting {agent_name}...")
        result = connector.connect(agent_name)
        if result["success"]:
            _print_ok(result["message"])
            if result.get("mcp_token"):
                _print_info(f"MCP token: {result['mcp_token']}")
        else:
            _print_err(result["message"])


def cmd_logs():
    """Tail EasyWiki server logs."""
    log_path = _log_file()
    if not log_path.exists():
        _print_err("No log file found. Is the server running?")
        return
    _print_info(f"Tailing {log_path} (Ctrl+C to stop)...")
    try:
        subprocess.run(["tail", "-f", str(log_path)])
    except KeyboardInterrupt:
        print()


def cmd_reset_password():
    """Reset admin password."""
    _print_header("Reset Admin Password")
    import secrets
    new_pw = secrets.token_urlsafe(12)

    try:
        import sqlite3
        from orgmind.auth.password import hash_password
        db_path = _get_easywiki_dir() / "easywiki.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("UPDATE users SET hashed_password=? WHERE email=?",
                     (hash_password(new_pw), "admin@local"))
        conn.commit()
        conn.close()
        _print_ok(f"Password reset to: {new_pw}")
        _print_info("Login: admin@local / " + new_pw)
    except Exception as e:
        _print_err(f"Failed: {e}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        # Show help
        _print_header("EasyWiki — Agent-Driven Knowledge Base")
        print(textwrap.dedent("""\
          Commands:
            start              Start EasyWiki server
            stop               Stop server
            status             Show server + agent status
            connect --auto     Auto-detect and connect all agents
            connect <agent>    Connect a specific agent (claude-code, codex, easycode)
            logs               Tail server logs
            reset-password     Reset admin password

          Quick start:
            easywiki start
            easywiki connect --auto
        """))
        return

    cmd = sys.argv[1]

    if cmd == "start":
        port = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 8080
        cmd_start(port=port)
    elif cmd == "stop":
        cmd_stop()
    elif cmd == "status":
        cmd_status()
    elif cmd == "connect":
        if len(sys.argv) > 2 and sys.argv[2] == "--auto":
            cmd_connect(auto=True)
        elif len(sys.argv) > 2:
            cmd_connect(agent_name=sys.argv[2])
        else:
            cmd_connect()
    elif cmd == "logs":
        cmd_logs()
    elif cmd == "reset-password":
        cmd_reset_password()
    else:
        print(f"Unknown command: {cmd}")
        print("Run 'easywiki' for help.")
        sys.exit(1)


if __name__ == "__main__":
    main()
