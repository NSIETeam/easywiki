#!/usr/bin/env python3
"""
EasyWiki Agent Connector — 自动检测 AI Agent 并写入 MCP 配置

支持的 Agent:
  - Claude Code  (~/.claude.json or ~/.config/claude-code/config.json)
  - Codex        (~/.codex/config.json or ~/.codex/config.toml)
  - EasyCode     (~/.easycode/settings.json)
  - Cursor       (~/.cursor/config.json)
  - Generic MCP  (任何支持 MCP stdio 的客户端)

核心原则：
  - 永不覆盖已有配置，只合并追加
  - 自动生成 MCP token
  - 检测 EasyWiki 服务是否在运行
"""
import os
import sys
import json
import shutil
import tempfile
from pathlib import Path
from datetime import datetime

# Resolve project root
_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent
_MCP_SERVER_SCRIPT = _HERE / "mcp_server" / "server.py"
_PYTHON_EXEC = sys.executable

# EasyWiki home — directory containing easywiki.db
_EW_HOME = Path(os.getenv("ORGMIND_DB_PATH", os.path.expanduser("~/.easywiki/easywiki.db"))).parent


class AgentConnector:
    """检测和连接 AI Agent 到 EasyWiki"""

    AGENT_CONFIGS = {
        "claude-code": {
            "name": "Claude Code",
            "config_paths": [
                Path.home() / ".claude.json",
                Path.home() / ".config" / "claude-code" / "config.json",
            ],
            "config_format": "json",
            "mcp_key": "mcpServers",
            "mcp_entry": {
                "command": _PYTHON_EXEC,
                "args": [str(_MCP_SERVER_SCRIPT)],
                "env": {},
            },
        },
        "codex": {
            "name": "Codex CLI",
            "config_paths": [
                Path.home() / ".codex" / "config.json",
                Path.home() / ".codex" / "config.toml",
            ],
            "config_format": "json",  # TOML handled separately
            "mcp_key": "mcp_servers",
            "mcp_entry": {
                "command": _PYTHON_EXEC,
                "args": [str(_MCP_SERVER_SCRIPT)],
                "env": {},
            },
        },
        "easycode": {
            "name": "EasyCode",
            "config_paths": [
                Path.home() / ".easycode" / "settings.json",
                Path.home() / ".easyclaw" / "mcp-config.json",
            ],
            "config_format": "json",
            "mcp_key": "mcpServers",
            "mcp_entry": {
                "command": _PYTHON_EXEC,
                "args": [str(_MCP_SERVER_SCRIPT)],
                "env": {},
            },
        },
        "cursor": {
            "name": "Cursor",
            "config_paths": [
                Path.home() / ".cursor" / "config.json",
                Path.home() / "Library" / "Application Support" / "Cursor" / "User" / "settings.json",
            ],
            "config_format": "json",
            "mcp_key": "mcp.servers",
            "mcp_entry": {
                "command": _PYTHON_EXEC,
                "args": [str(_MCP_SERVER_SCRIPT)],
                "env": {},
            },
        },
    }

    def detect_all_agents(self) -> list:
        """检测本机所有已安装的 AI Agent"""
        detected = []
        for agent_type, config in self.AGENT_CONFIGS.items():
            info = self._detect_agent(agent_type, config)
            if info:
                detected.append(info)
        return detected

    def _detect_agent(self, agent_type: str, config: dict) -> dict | None:
        """检测单个 agent 是否安装"""
        # Check by binary presence
        binary_names = {
            "claude-code": ["claude"],
            "codex": ["codex"],
            "easycode": ["easycode"],
            "cursor": ["cursor"],
        }
        binary_found = False
        for bin_name in binary_names.get(agent_type, []):
            if shutil.which(bin_name):
                binary_found = True
                break

        # Check by config file presence
        config_found = None
        for path in config["config_paths"]:
            if path.exists():
                config_found = str(path)
                break

        # Also check for running processes or other markers
        if not binary_found and not config_found:
            # Special checks
            if agent_type == "easycode":
                if (Path.home() / ".easyclaw").exists():
                    binary_found = True
                if (Path.home() / ".easycode-user").exists():
                    binary_found = True
            if agent_type == "claude-code":
                if (Path.home() / ".claude").exists():
                    binary_found = True

        if not binary_found and not config_found:
            return None

        # Check if already connected
        connected = False
        if config_found:
            try:
                with open(config_found) as f:
                    data = json.load(f)
                mcp_key = config["mcp_key"]
                if "." in mcp_key:
                    parts = mcp_key.split(".")
                    val = data
                    for p in parts:
                        val = val.get(p, {}) if isinstance(val, dict) else {}
                    connected = "easywiki" in val if isinstance(val, dict) else False
                else:
                    connected = "easywiki" in data.get(mcp_key, {})
            except Exception:
                pass

        return {
            "type": agent_type,
            "name": config["name"],
            "binary": binary_found,
            "config_path": config_found,
            "connected": connected,
        }

    def connect(self, agent_type: str) -> dict:
        """连接 agent — 写入 MCP 配置"""
        if agent_type not in self.AGENT_CONFIGS:
            return {"success": False, "message": f"Unknown agent: {agent_type}"}

        config = self.AGENT_CONFIGS[agent_type]

        # Ensure MCP token exists
        mcp_token = self._ensure_mcp_token()

        # Build MCP entry with token in env
        mcp_entry = dict(config["mcp_entry"])
        mcp_entry["env"] = {"EASYWIKI_MCP_TOKEN": mcp_token}

        # Find or create config file
        config_path = None
        for path in config["config_paths"]:
            if path.exists():
                config_path = path
                break

        if not config_path:
            # Create in the first configured path
            config_path = config["config_paths"][0]
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text("{}")
            _log(f"Created config file: {config_path}")

        # Read existing config
        try:
            with open(config_path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            data = {}

        # Write MCP config (merge, never overwrite)
        mcp_key = config["mcp_key"]
        if "." in mcp_key:
            # Nested key (e.g., "mcp.servers")
            parts = mcp_key.split(".")
            target = data
            for p in parts[:-1]:
                if p not in target or not isinstance(target[p], dict):
                    target[p] = {}
                target = target[p]
            key = parts[-1]
            if key not in target:
                target[key] = {}
            if "easywiki" in target[key]:
                return {"success": True, "message": "Already connected (config exists)", "mcp_token": mcp_token}
            target[key]["easywiki"] = mcp_entry
        else:
            if mcp_key not in data:
                data[mcp_key] = {}
            if "easywiki" in data[mcp_key]:
                return {"success": True, "message": "Already connected (config exists)", "mcp_token": mcp_token}
            data[mcp_key]["easywiki"] = mcp_entry

        # Backup and write
        self._safe_write(config_path, data)

        # Verify server is running
        server_ok = self._check_server()

        return {
            "success": True,
            "message": f"MCP config written to {config_path}" + (
                "" if server_ok else " (⚠️ Start EasyWiki server first: easywiki start)"
            ),
            "mcp_token": mcp_token,
            "config_path": str(config_path),
        }

    def _ensure_mcp_token(self) -> str:
        """生成或读取 MCP token"""
        _EW_HOME.mkdir(parents=True, exist_ok=True)
        token_path = _EW_HOME / "mcp_token"
        if token_path.exists():
            return token_path.read_text().strip()

        import secrets
        token = secrets.token_urlsafe(32)

        # Also register this token in the DB so the API accepts it
        self._register_token_in_db(token)

        token_path.write_text(token)
        token_path.chmod(0o600)
        return token

    def _register_token_in_db(self, token: str):
        """在数据库中注册 MCP token，使 API 能验证"""
        try:
            import sqlite3
            db_path = _EW_HOME / "easywiki.db"
            if not db_path.exists():
                _log(f"DB not found at {db_path}, token will be validated on first start")
                return
            conn = sqlite3.connect(str(db_path))
            # Create token table if not exists
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mcp_tokens (
                    token TEXT PRIMARY KEY,
                    created_at TEXT DEFAULT (datetime('now')),
                    last_used TEXT
                )
            """)
            conn.execute("INSERT OR REPLACE INTO mcp_tokens (token) VALUES (?)", (token,))
            conn.commit()
            conn.close()
        except Exception as e:
            _log(f"Failed to register MCP token in DB: {e}")

    def _check_server(self) -> bool:
        """检查 EasyWiki 服务是否在运行"""
        import socket
        try:
            with socket.create_connection(("127.0.0.1", 8080), timeout=1):
                return True
        except (OSError, ConnectionRefusedError):
            return False

    def _safe_write(self, path: Path, data: dict):
        """安全写入 — 先写临时文件，再原子替换"""
        path.parent.mkdir(parents=True, exist_ok=True)
        # Backup
        if path.exists():
            backup = path.with_suffix(path.suffix + ".easywiki-backup")
            shutil.copy2(path, backup)
        # Write to temp then rename
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        tmp.rename(path)
        _log(f"Updated config: {path}")

    def generate_mcp_config_snippet(self) -> str:
        """生成 MCP 配置片段（用于手动配置）"""
        mcp_token = self._ensure_mcp_token()
        return json.dumps({
            "easywiki": {
                "command": _PYTHON_EXEC,
                "args": [str(_MCP_SERVER_SCRIPT)],
                "env": {"EASYWIKI_MCP_TOKEN": mcp_token}
            }
        }, indent=2, ensure_ascii=False)


def _log(msg: str):
    """写入日志"""
    log_path = _EW_HOME / "connector.log"
    try:
        with open(log_path, "a") as f:
            f.write(f"[{datetime.now().isoformat()}] {msg}\n")
    except Exception:
        pass


# ── Session Hooks ────────────────────────────────────────────────────────────

def on_session_start(session_id: str = None, project_id: str = None, query: str = None) -> dict:
    """
    会话开始时自动搜索相关记忆并返回。
    Agent 启动时调用此函数，获取与当前任务相关的历史知识。

    Usage from MCP server or agent hook:
        from orgmind.connector import on_session_start
        context = on_session_start(query="deploy easywiki to server")
    """
    import urllib.request

    if not query:
        return {"memories": [], "message": "No query provided"}

    token = _get_system_token()
    if not token:
        return {"memories": [], "message": "Could not generate system token — is EasyWiki initialized?"}

    try:
        if not query:
            return {"memories": [], "message": "No query provided"}

        body = json.dumps({"query": query, "top_k": 5}).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:8080/api/v1/retrieve",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {_get_system_token()}",
            },
            method="POST",
        )
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read())

        memories = []
        for r in data.get("results", []):
            memories.append({
                "content": r.get("content_snippet", ""),
                "score": r.get("score", 0),
                "type": r.get("source_type", "memory"),
            })

        return {
            "memories": memories,
            "total": len(memories),
            "message": f"Found {len(memories)} relevant memories" if memories else "No relevant memories found",
        }
    except Exception as e:
        return {"memories": [], "error": str(e)}


def on_session_end(session_text: str, session_id: str = None, project_id: str = None) -> dict:
    """
    会话结束时自动提取记忆并提报。
    Agent 结束时调用此函数，自动从会话文本中提取知识沉淀到 EasyWiki。

    Usage from MCP server or agent hook:
        from orgmind.connector import on_session_end
        result = on_session_end(session_text="...", project_id="...")
    """
    import urllib.request

    token = _get_system_token()
    if not token:
        return {"written": 0, "message": "Could not generate system token — is EasyWiki initialized?"}

    try:
        body = json.dumps({
            "session_text": session_text[:8000],
            "session_id": session_id,
        }).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:8080/api/v1/session/auto-record",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {_get_system_token()}",
            },
            method="POST",
        )
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())

        return {
            "written": data.get("memories_written", 0),
            "total_extracted": data.get("total_extracted", 0),
            "memories": data.get("memories", []),
            "skill_candidate": data.get("skill_candidate"),
            "message": f"Extracted {data.get('total_extracted', 0)} memories, wrote {data.get('memories_written', 0)}",
        }
    except Exception as e:
        return {"written": 0, "error": str(e)}


def _ensure_mcp_token_safe() -> str:
    """安全读取 MCP token"""
    token_path = _EW_HOME / "mcp_token"
    if token_path.exists():
        return token_path.read_text().strip()
    return ""


def _get_system_token() -> str:
    """
    获取系统级 JWT token 用于内部 API 调用。
    生成一个 admin 级别的短期 token。
    """
    try:
        import sqlite3
        import sys as _sys
        # Ensure project root is on path
        _root = str(Path(__file__).resolve().parent.parent)
        if _root not in _sys.path:
            _sys.path.insert(0, _root)
        from orgmind.auth.jwt import create_token

        db_path = _EW_HOME / "easywiki.db"
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute("SELECT id, org_id, role, department_id FROM users WHERE email='admin@local'")
        row = cur.fetchone()
        conn.close()

        if row:
            return create_token(user_id=row[0], org_id=row[1], role=row[2],
                                department_id=row[3], project_ids=[])
    except Exception as e:
        _log(f"Failed to get system token: {e}")
    return ""
