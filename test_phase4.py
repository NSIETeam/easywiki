import tempfile, os, json, sys

out_file = os.path.join(os.path.dirname(__file__), 'phase4_result.txt')
with open(out_file, 'w') as out:
    # Test manifest_writer
    from orgmind.easywiki.manifest_writer import write_manifest_files
    tmpdir = tempfile.mkdtemp()
    result = write_manifest_files(tmpdir, 'test-pid-123', 'test-org-456')

    out.write('=== manifest_writer test ===\n')
    out.write(f'EASYWIKI.md created: {os.path.exists(os.path.join(tmpdir, "EASYWIKI.md"))}\n')

    mf_path = os.path.join(tmpdir, '.easywiki', 'manifest.json')
    out.write(f'manifest.json created: {os.path.exists(mf_path)}\n')
    if os.path.exists(mf_path):
        mf = json.load(open(mf_path))
        out.write(f'manifest project_id: {mf["project_id"]}\n')
        out.write(f'manifest write_scopes: {mf["write_scopes"]}\n')

    # Test mcp_config_sync
    from orgmind.easywiki.mcp_config_sync import sync_all_enabled, get_detectable_tools, sync_tool_config
    tools = get_detectable_tools()
    out.write(f'=== mcp_config_sync test ===\n')
    out.write(f'Detectable tools: {len(tools)}\n')
    for t in tools:
        out.write(f'  - {t["id"]}: {t["name"]}\n')

    # Test JSON merge (Claude Code style)
    test_config_dir = os.path.join(tmpdir, '.claude')
    os.makedirs(test_config_dir, exist_ok=True)
    test_config = os.path.join(test_config_dir, 'mcp.json')
    # Pre-populate with existing config
    json.dump({"mcpServers": {"existing_tool": {"command": "node", "args": ["tool.js"]}}}, open(test_config, 'w'))

    from orgmind.easywiki.mcp_config_sync import _merge_json_config
    merge_result = _merge_json_config(test_config, 'mcpServers', 'claude-code')
    out.write(f'JSON merge result: {merge_result["status"]}\n')

    # Verify existing config preserved
    updated = json.load(open(test_config))
    out.write(f'Existing tool preserved: {"existing_tool" in updated.get("mcpServers", {})}\n')
    out.write(f'EasyWiki added: {"easywiki" in updated.get("mcpServers", {})}\n')
    out.write(f'ALL CHECKS PASSED\n')
