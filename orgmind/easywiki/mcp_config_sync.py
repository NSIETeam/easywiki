"""
MCP Config Sync — detect and write MCP config for agent tools.
Section 6.5 of EASYWIKI_EXECUTION_SPEC.md

Key rule: MUST merge with existing config, NEVER overwrite.
"""
import os
import json
import shutil
from typing import List, Dict

from orgmind.agent_detector import detect_agents

# MCP Server configuration that gets injected into each tool's config
MCP_SERVER_ENTRY = {
    "command": "python",
    "args": ["-m", "orgmind.mcp_server.server"]
}

# Known tool config file paths (relative to project or home)
TOOL_CONFIGS = {
    "claude-code": {
        "paths": [".claude/mcp.json", ".mcp.json"],
        "type": "json",
        "key": "mcpServers",
    },
    "codex": {
        "paths": [os.path.expanduser("~/.codex/config.toml")],
        "type": "toml",
        "key": "mcp_servers",
    },
    "workbuddy": {
        "paths": ["mcp.json", os.path.expanduser("~/mcp.json")],
        "type": "json",
        "key": "mcpServers",
    },
    "easycode": {
        "paths": [".easycode/mcp.json", "easycode_mcp.json"],
        "type": "json",
        "key": "mcpServers",
    },
}


def sync_tool_config(project_root: str, tool_id: str) -> dict:
    """
    Attempt to write MCP config for a specific tool.
    Returns: {"status": "ok"|"skipped"|"not_found"|"error", "message": str}
    """
    if tool_id not in TOOL_CONFIGS:
        return {"status": "skipped", "message": f"Unknown tool: {tool_id}"}

    config_info = TOOL_CONFIGS[tool_id]

    # Try each possible config path
    for rel_path in config_info["paths"]:
        if os.path.isabs(rel_path):
            config_path = rel_path
        else:
            config_path = os.path.join(project_root, rel_path)

        config_dir = os.path.dirname(config_path)
        if config_dir and not os.path.exists(config_dir):
            continue  # Skip if directory doesn't exist

        if config_info["type"] == "json":
            return _merge_json_config(config_path, config_info["key"], tool_id)
        elif config_info["type"] == "toml":
            return _merge_toml_config(config_path, config_info["key"], tool_id)

    return {"status": "not_found", "message": f"No config file found for {tool_id} in project {project_root}"}


def _merge_json_config(config_path: str, key: str, tool_id: str) -> dict:
    """Merge EasyWiki MCP entry into an existing JSON config file."""
    # Read existing config
    existing = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            return {"status": "error", "message": f"Failed to read {config_path}: {e}"}

    # The config might have mcpServers at root or nested
    if key not in existing:
        existing[key] = {}

    # Add/update easywiki entry
    existing[key]["easywiki"] = dict(MCP_SERVER_ENTRY)

    # Write back
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        return {"status": "ok", "message": f"Updated {config_path}", "path": config_path}
    except IOError as e:
        return {"status": "error", "message": f"Failed to write {config_path}: {e}"}


def _merge_toml_config(config_path: str, key: str, tool_id: str) -> dict:
    """Merge EasyWiki MCP entry into a TOML config file (Codex)."""
    existing_lines = []
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                existing_lines = f.readlines()
        except IOError as e:
            return {"status": "error", "message": f"Failed to read {config_path}: {e}"}

    # Check if easywiki section already exists
    easywiki_section = f"[{key}.easywiki]"
    has_section = any(easywiki_section in line for line in existing_lines)

    if has_section:
        return {"status": "skipped", "message": f"easywiki section already exists in {config_path}"}

    # Append new section
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    try:
        with open(config_path, "a", encoding="utf-8") as f:
            if existing_lines and not existing_lines[-1].endswith("\n"):
                f.write("\n")
            f.write(f"\n[{key}.easywiki]\n")
            f.write(f'command = "{MCP_SERVER_ENTRY["command"]}"\n')
            f.write(f'args = {json.dumps(MCP_SERVER_ENTRY["args"])}\n')
        return {"status": "ok", "message": f"Appended to {config_path}", "path": config_path}
    except IOError as e:
        return {"status": "error", "message": f"Failed to write {config_path}: {e}"}


def sync_all_enabled(project_root: str, enabled_tool_ids: List[str]) -> Dict:
    """
    Sync MCP config for all enabled tools.
    Returns summary of results.
    """
    installed = {a["id"]: a for a in detect_agents()}
    results = {}

    for tool_id in enabled_tool_ids:
        if tool_id not in installed:
            results[tool_id] = {"status": "not_detected", "message": f"Tool {tool_id} not found on this machine"}
            continue
        results[tool_id] = sync_tool_config(project_root, tool_id)

    return {
        "project_root": project_root,
        "enabled": enabled_tool_ids,
        "results": results,
    }


def get_detectable_tools() -> List[Dict]:
    """Get list of detectable agents on this machine (pass-through to agent_detector)."""
    return detect_agents()
