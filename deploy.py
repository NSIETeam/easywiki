import paramiko, os, json

host = '60.205.220.121'
user = 'king'
password = '123456'
out_path = os.path.join(os.path.dirname(__file__), 'deploy_log.json')

logs = []

def run_cmd(client, cmd, desc=""):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=120)
    out = stdout.read().decode()
    err = stderr.read().decode()
    logs.append({"desc": desc, "cmd": cmd, "out": out[:500], "err": err[:500], "exit": stdout.channel.recv_exit_status()})
    return out, err

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=30, allow_agent=False, look_for_keys=False)
    logs.append({"step": "connected"})

    # Check if project already exists
    out, _ = run_cmd(client, "ls ~/OrgMind/orgmind/main_sqlite.py 2>/dev/null && echo EXISTS || echo NOT_FOUND", "check existing")
    exists = "EXISTS" in out
    logs.append({"existing_project": exists})

    if not exists:
        # Create directory structure
        run_cmd(client, "mkdir -p ~/OrgMind/orgmind/easywiki ~/OrgMind/orgmind/mcp_server ~/OrgMind/orgmind/governance ~/OrgMind/orgmind/services ~/OrgMind/orgmind/graph ~/OrgMind/orgmind/auth ~/OrgMind/orgmind/skills ~/OrgMind/orgmind/agents ~/OrgMind/orgmind/retrieval ~/OrgMind/orgmind/tools ~/OrgMind/orgmind/models ~/OrgMind/frontend/dist ~/OrgMind/docs", "create dirs")
        logs.append({"dirs_created": True})

    # Upload key files via SFTP
    sftp = client.open_sftp()
    local_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    files_to_upload = [
        "orgmind/main_sqlite.py",
        "orgmind/database_sqlite.py",
        "orgmind/config.py",
        "orgmind/agent_detector.py",
        "orgmind/desktop_shell.py",
        "orgmind/governance/cleaners.py",
        "orgmind/governance/pii.py",
        "orgmind/governance/quality.py",
        "orgmind/governance/dedup.py",
        "orgmind/governance/__init__.py",
        "orgmind/services/embedding.py",
        "orgmind/services/audit.py",
        "orgmind/services/write_queue.py",
        "orgmind/services/auto_memory.py",
        "orgmind/services/__init__.py",
        "orgmind/auth/password.py",
        "orgmind/auth/__init__.py",
        "orgmind/easywiki/__init__.py",
        "orgmind/easywiki/routes.py",
        "orgmind/easywiki/version_diff.py",
        "orgmind/easywiki/graph_lite.py",
        "orgmind/easywiki/manifest_writer.py",
        "orgmind/easywiki/mcp_config_sync.py",
        "orgmind/easywiki/pending_entry.py",
        "orgmind/mcp_server/__init__.py",
        "orgmind/mcp_server/server.py",
        "docs/EASYWIKI_PRODUCT_DESIGN.md",
        "docs/EASYWIKI_EXECUTION_SPEC.md",
    ]
    uploaded = []
    for f in files_to_upload:
        local_path = os.path.join(local_root, f)
        remote_path = f"OrgMind/{f}"
        if os.path.exists(local_path):
            try:
                sftp.put(local_path, remote_path)
                uploaded.append(f)
            except Exception as e:
                logs.append({"upload_error": f, "error": str(e)})
    sftp.close()
    logs.append({"uploaded": len(uploaded), "files": uploaded})

    # Create missing __init__.py files
    run_cmd(client, "touch ~/OrgMind/orgmind/__init__.py ~/OrgMind/orgmind/governance/__init__.py ~/OrgMind/orgmind/services/__init__.py ~/OrgMind/orgmind/auth/__init__.py", "create inits")

    # Install Python deps
    out, err = run_cmd(client, "cd ~/OrgMind && pip3 install fastapi uvicorn jwt bcrypt numpy jieba openai sentence-transformers pyjwt 2>&1 | tail -5", "install python deps")

    # Install MCP SDK
    run_cmd(client, "pip3 install mcp 2>&1 | tail -3", "install mcp sdk")

    # Start backend
    run_cmd(client, "cd ~/OrgMind && nohup python3 -m uvicorn orgmind.main_sqlite:app --host 0.0.0.0 --port 8080 > /tmp/orgmind.log 2>&1 & echo 'started'", "start backend")

    import time
    time.sleep(3)

    # Check backend
    out, _ = run_cmd(client, "curl -s http://127.0.0.1:8080/health 2>&1 || echo 'NOT_RUNNING'", "check backend")
    logs.append({"backend_health": out.strip()})

    client.close()
except Exception as e:
    logs.append({"fatal_error": str(e)})

with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(logs, f, ensure_ascii=False, indent=2)
print("DEPLOY_DONE")
