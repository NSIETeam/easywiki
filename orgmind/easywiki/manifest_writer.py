"""
Manifest Writer — generates EASYWIKI.md + .easywiki/manifest.json in project root.
Section 6.1 and 6.2 of EASYWIKI_EXECUTION_SPEC.md
"""
import os
import json
import sys


EASYWIKI_MD_TEMPLATE = """# EasyWiki 已接入本项目

本项目已连接 EasyWiki 知识库（project_id: {project_id}）。

## 你可以使用的工具（通过 MCP）
- `search_knowledge` — 开始任务前，先搜索是否有相关的历史决策/最佳实践/踩坑记录
- `get_project_manifest` — 获取本项目的栏位结构
- `propose_entry` — 完成一个关键动作（决策/修复bug/确定架构）后，提报一条记录
- `propose_session_summary` — 会话/任务结束时，提报压缩后的过程摘要（不是原始对话记录，是结构化摘要）
- `propose_progress_update` — 任务状态变化时，提报进度表建议更新
- `get_pending_status` — 查询你之前的提报是否已被人工确认

## 重要行为准则
1. 所有 propose_* 调用**不会立即生效**，会进入人工审核队列（Agent Inbox），必须等待人工批准才正式写入知识库。
2. 提报内容要精炼、结构化，避免把原始对话/代码贴进去，只提炼"发生了什么/决定了什么/为什么"。
3. 每次开始新任务前，优先调用 search_knowledge 查是否有人已经踩过同样的坑。
"""

MANIFEST_TEMPLATE = {
    "project_id": "{project_id}",
    "org_id": "{org_id}",
    "mcp_stdio_command": "python",
    "mcp_stdio_args": ["-m", "orgmind.mcp_server.server"],
    "mcp_working_dir": "{easywiki_root}",
    "write_scopes": ["decision", "bug_fix", "best_practice", "architecture", "progress_update", "session_summary"]
}


def write_manifest_files(project_root: str, project_id: str, org_id: str) -> dict:
    """
    Write EASYWIKI.md and .easywiki/manifest.json to the project root.
    Returns summary of what was written.
    """
    easywiki_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    result = {"files": []}

    # Write EASYWIKI.md
    md_path = os.path.join(project_root, "EASYWIKI.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(EASYWIKI_MD_TEMPLATE.format(project_id=project_id))
    result["files"].append({"path": md_path, "type": "discovery"})

    # Write .easywiki/manifest.json
    easywiki_dir = os.path.join(project_root, ".easywiki")
    os.makedirs(easywiki_dir, exist_ok=True)
    manifest_path = os.path.join(easywiki_dir, "manifest.json")
    manifest = dict(MANIFEST_TEMPLATE)
    manifest["project_id"] = project_id
    manifest["org_id"] = org_id
    manifest["mcp_working_dir"] = easywiki_root
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    result["files"].append({"path": manifest_path, "type": "manifest"})

    return result
