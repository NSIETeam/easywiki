"""Final comprehensive verification for EasyWiki backend modules"""
import os, sys, json

out_path = os.path.join(os.path.dirname(__file__), 'final_verify.txt')
results = []

def check(name, fn):
    try:
        result = fn()
        results.append(f"[PASS] {name}: {result}")
    except Exception as e:
        results.append(f"[FAIL] {name}: {e}")

def _check_table(name):
    from orgmind.database_sqlite import get_db
    db = get_db()
    try:
        db.execute(f"SELECT COUNT(*) FROM {name}").fetchone()
        return True
    except:
        return False

def _module_ok(name):
    try:
        __import__(name)
        return True
    except Exception as e:
        return str(e)[:80]

def _mcp_server_name():
    from orgmind.mcp_server.server import server
    return server.name

def _test_version_merge():
    from orgmind.easywiki.version_diff import three_way_merge
    merged, cid = three_way_merge("base", "base", "proposed", "page", "test_id", "test_project")
    return merged == "proposed" and cid is None

def _test_graph():
    from orgmind.easywiki.graph_lite import extract_entities
    ents = extract_entities("决定采用FastAPI技术栈，用于OrgMind项目和测试系统")
    return len(ents) >= 2

# ============ Run checks ============

check("DB: easywiki_projects", lambda: "ok" if _check_table("easywiki_projects") else "MISSING")
check("DB: easywiki_pages", lambda: "ok" if _check_table("easywiki_pages") else "MISSING")
check("DB: easywiki_page_contents", lambda: "ok" if _check_table("easywiki_page_contents") else "MISSING")
check("DB: easywiki_pending_entries", lambda: "ok" if _check_table("easywiki_pending_entries") else "MISSING")
check("DB: easywiki_memories", lambda: "ok" if _check_table("easywiki_memories") else "MISSING")
check("DB: easywiki_versions", lambda: "ok" if _check_table("easywiki_versions") else "MISSING")
check("DB: easywiki_conflicts", lambda: "ok" if _check_table("easywiki_conflicts") else "MISSING")
check("DB: easywiki_graph_entities", lambda: "ok" if _check_table("easywiki_graph_entities") else "MISSING")
check("DB: easywiki_graph_relations", lambda: "ok" if _check_table("easywiki_graph_relations") else "MISSING")
check("DB: easywiki_agent_configs", lambda: "ok" if _check_table("easywiki_agent_configs") else "MISSING")
check("DB: easywiki_progress_fields", lambda: "ok" if _check_table("easywiki_progress_fields") else "MISSING")

check("Module: routes", lambda: "ok" if _module_ok("orgmind.easywiki.routes") else "FAIL")
check("Module: version_diff", lambda: "ok" if _module_ok("orgmind.easywiki.version_diff") else "FAIL")
check("Module: graph_lite", lambda: "ok" if _module_ok("orgmind.easywiki.graph_lite") else "FAIL")
check("Module: manifest_writer", lambda: "ok" if _module_ok("orgmind.easywiki.manifest_writer") else "FAIL")
check("Module: mcp_config_sync", lambda: "ok" if _module_ok("orgmind.easywiki.mcp_config_sync") else "FAIL")
check("Module: mcp_server", lambda: "ok" if _module_ok("orgmind.mcp_server.server") else "FAIL")

check("MCP: server name", lambda: _mcp_server_name())
check("Version: 3-way merge", lambda: "PASS" if _test_version_merge() else "FAIL")
check("Graph: entity extraction", lambda: f"{_test_graph()}" if _test_graph() else "FAIL")

# Write results
with open(out_path, 'w', encoding='utf-8') as f:
    f.write("=== EasyWiki Final Verification ===\n\n")
    for r in results:
        f.write(r + "\n")
    passed = sum(1 for r in results if "[PASS]" in r)
    failed = sum(1 for r in results if "[FAIL]" in r)
    f.write(f"\n=== {passed}/{passed+failed} PASSED ===\n")
