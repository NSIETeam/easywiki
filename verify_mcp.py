"""Quick MCP server verification"""
from orgmind.mcp_server.server import server
import asyncio

async def main():
    tools = await server._tool_manager.list_tools()
    names = [t.name for t in tools]
    result = {
        "server_name": server.name,
        "tool_count": len(tools),
        "tool_names": names,
        "expected_6": len(tools) == 6,
        "names_match": names == ['search_knowledge','get_project_manifest','propose_entry','propose_session_summary','propose_progress_update','get_pending_status']
    }
    import json, os
    out = os.path.join(os.path.dirname(__file__), 'mcp_verify.json')
    json.dump(result, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print("DONE")

asyncio.run(main())
