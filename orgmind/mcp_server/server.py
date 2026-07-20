"""
EasyWiki MCP Server — Section 6.3 of EASYWIKI_EXECUTION_SPEC.md
Usage: python -m orgmind.mcp_server.server
(Intended to be spawned as a stdio subprocess by MCP clients — Claude Code, Codex, etc.)
"""
import json
import urllib.request
import sys
import asyncio
import os

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# ================================================================
# Server instance — must be created before decorators are applied
# ================================================================
server = Server("easywiki")

BASE_URL = "http://127.0.0.1:8080"
MCP_TOKEN = os.environ.get("EASYWIKI_MCP_TOKEN", "")
if not MCP_TOKEN:
    token_path = os.path.expanduser("~/.easywiki/mcp_token")
    try:
        with open(token_path, "r", encoding="utf-8") as token_file:
            MCP_TOKEN = token_file.read().strip()
    except OSError:
        MCP_TOKEN = ""


def _http_req(method: str, path: str, body: dict = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if MCP_TOKEN:
        headers["Authorization"] = f"Bearer {MCP_TOKEN}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(f"{BASE_URL}{path}", data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = json.loads(e.read())
        return {"error": str(e.code), "detail": err}


# ================================================================
# Tool registration
# ================================================================
@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_knowledge",
            description="搜索EasyWiki知识库的历史决策、最佳实践和踩坑记录。开始新任务前搜索可避免重复犯错。",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "project_id": {"type": "string", "description": "项目ID"},
                    "top_k": {"type": "integer", "default": 5, "description": "返回条数"},
                },
                "required": ["query", "project_id"]
            }
        ),
        Tool(
            name="get_project_manifest",
            description="获取项目的固定栏位结构和进度表字段定义。",
            inputSchema={
                "type": "object",
                "properties": {"project_id": {"type": "string"}},
                "required": ["project_id"]
            }
        ),
        Tool(
            name="propose_entry",
            description="完成关键动作（决策/修复Bug/确定架构）后提报一条记录到EasyWiki。提报进入待审核队列，不会立即生效。",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "session_id": {"type": "string"},
                    "tool_name": {"type": "string"},
                    "entry_type": {"type": "string", "enum": ["decision", "bug_fix", "best_practice", "architecture"]},
                    "target_section": {"type": "string"},
                    "content": {"type": "string"},
                    "file_refs": {"type": "array", "items": {"type": "string"}, "default": []},
                    "confidence": {"type": "number", "default": 0.7},
                },
                "required": ["project_id", "session_id", "tool_name", "entry_type", "target_section", "content"]
            }
        ),
        Tool(
            name="propose_session_summary",
            description="会话结束时提报压缩摘要。自动从长文本中提取结构化条目后提交审核。",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "session_id": {"type": "string"},
                    "tool_name": {"type": "string"},
                    "session_text": {"type": "string", "description": "完整会话文本"},
                },
                "required": ["project_id", "session_id", "tool_name", "session_text"]
            }
        ),
        Tool(
            name="propose_progress_update",
            description="任务状态变化时提报进度表建议更新。",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "session_id": {"type": "string"},
                    "tool_name": {"type": "string"},
                    "field_name": {"type": "string"},
                    "suggested_value": {"type": "string"},
                },
                "required": ["project_id", "session_id", "tool_name", "field_name", "suggested_value"]
            }
        ),
        Tool(
            name="get_pending_status",
            description="查询之前提报的记录审核状态。",
            inputSchema={
                "type": "object",
                "properties": {"entry_id": {"type": "string"}},
                "required": ["entry_id"]
            }
        ),
        # New: Session lifecycle hooks for zero-config knowledge capture
        Tool(
            name="recall_context",
            description="会话开始时调用：搜索知识库中与当前任务相关的历史记忆，避免重复踩坑。每次开始新任务时自动调用。",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "当前任务描述或关键词"},
                    "top_k": {"type": "integer", "default": 5},
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="save_session",
            description="会话结束时调用：自动从对话文本中提取决策、Bug修复、最佳实践等知识并沉淀到EasyWiki。每次会话结束时自动调用。",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_text": {"type": "string", "description": "完整会话文本"},
                    "session_id": {"type": "string", "description": "会话ID"},
                },
                "required": ["session_text"]
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "search_knowledge":
            body = {"query": arguments["query"], "top_k": arguments.get("top_k", 5)}
            result = _http_req("POST", "/api/v1/retrieve", body)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

        elif name == "get_project_manifest":
            pid = arguments["project_id"]
            result = _http_req("GET", f"/api/v1/easywiki/projects/{pid}/manifest")
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

        elif name == "propose_entry":
            body = {
                "project_id": arguments["project_id"],
                "session_id": arguments["session_id"],
                "tool_name": arguments["tool_name"],
                "entry_type": arguments["entry_type"],
                "target_section": arguments["target_section"],
                "content": arguments["content"],
                "file_refs": arguments.get("file_refs", []),
                "confidence": arguments.get("confidence", 0.7),
            }
            result = _http_req("POST", "/api/v1/easywiki/pending-entries", body)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

        elif name == "propose_session_summary":
            session_text = arguments["session_text"]
            try:
                from orgmind.services.auto_memory import extract_memories_from_session
                memories = extract_memories_from_session(session_text)
            except Exception as e:
                return [TextContent(type="text", text=json.dumps(
                    {"error": f"Memory extraction failed: {str(e)}", "raw_length": len(session_text)}, ensure_ascii=False))]

            if not memories:
                return [TextContent(type="text", text=json.dumps(
                    {"status": "no_memories_extracted", "message": "未从会话文本中提取到可沉淀的记忆条目。"}, ensure_ascii=False))]

            results = []
            for mem in memories:
                body = {
                    "project_id": arguments["project_id"],
                    "session_id": arguments["session_id"],
                    "tool_name": arguments["tool_name"],
                    "entry_type": mem.get("type", "episodic"),
                    "target_section": "decisions_experience",
                    "content": mem["content"],
                    "file_refs": [],
                    "confidence": mem.get("confidence", 0.7),
                }
                r = _http_req("POST", "/api/v1/easywiki/pending-entries", body)
                results.append(r)
            return [TextContent(type="text", text=json.dumps(
                {"extracted": len(memories), "submitted": len(results), "entries": results}, ensure_ascii=False, indent=2))]

        elif name == "propose_progress_update":
            content = json.dumps({
                "field_name": arguments["field_name"],
                "suggested_value": arguments["suggested_value"]
            })
            body = {
                "project_id": arguments["project_id"],
                "session_id": arguments["session_id"],
                "tool_name": arguments["tool_name"],
                "entry_type": "progress_update",
                "target_section": "progress_table",
                "content": content,
                "file_refs": [],
            }
            result = _http_req("POST", "/api/v1/easywiki/pending-entries", body)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

        elif name == "get_pending_status":
            eid = arguments["entry_id"]
            result = _http_req("GET", f"/api/v1/easywiki/pending-entries/{eid}")
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

        elif name == "recall_context":
            # Session start hook — search for relevant memories
            query = arguments["query"]
            top_k = arguments.get("top_k", 5)
            result = _http_req("POST", "/api/v1/retrieve", {"query": query, "top_k": top_k})
            memories = result.get("results", [])
            if memories:
                summary_lines = [f"Found {len(memories)} relevant memories from EasyWiki:"]
                for i, m in enumerate(memories, 1):
                    summary_lines.append(f"\n{i}. [score={m.get('score', 0):.2f}] {m.get('content_snippet', '')[:200]}")
                return [TextContent(type="text", text="\n".join(summary_lines))]
            else:
                return [TextContent(type="text", text="No relevant memories found in EasyWiki knowledge base.")]

        elif name == "save_session":
            # Session end hook — auto-extract and save memories
            session_text = arguments["session_text"]
            session_id = arguments.get("session_id", "")
            from orgmind.connector import on_session_end
            result = on_session_end(session_text=session_text, session_id=session_id)
            if result.get("written", 0) > 0:
                return [TextContent(type="text", text=json.dumps({
                    "status": "saved",
                    "written": result["written"],
                    "total_extracted": result.get("total_extracted", 0),
                    "message": f"EasyWiki auto-saved {result['written']} memories from this session."
                }, ensure_ascii=False, indent=2))]
            else:
                return [TextContent(type="text", text=json.dumps({
                    "status": "no_memories",
                    "message": "No extractable memories found in this session."
                }, ensure_ascii=False))]

        else:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
