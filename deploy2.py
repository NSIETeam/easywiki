import paramiko, os, json, time

host = '60.205.220.121'
user = 'king'
password = '123456'
out_path = os.path.join(os.path.dirname(__file__), 'deploy2_log.json')
logs = []

def run_cmd(client, cmd, desc="", timeout=120):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode()
    err = stderr.read().decode()
    exit_code = stdout.channel.recv_exit_status()
    logs.append({"desc": desc, "out": out[:800], "err": err[:300], "exit": exit_code})
    return out, err

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=30, allow_agent=False, look_for_keys=False)
    logs.append({"step": "connected"})

    # Upload remaining needed files
    sftp = client.open_sftp()
    local_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    extra_files = [
        "orgmind/services/employee_profile.py",
        "orgmind/services/__init__.py",
        "orgmind/config_demo.py",
    ]
    for f in extra_files:
        local_path = os.path.join(local_root, f)
        if os.path.exists(local_path):
            sftp.put(local_path, f"OrgMind/{f}")
            logs.append({"uploaded": f})
    sftp.close()

    # Ensure __init__.py everywhere
    run_cmd(client, "find ~/OrgMind/orgmind -type d -exec touch {}/__init__.py \\; 2>/dev/null; echo done", "ensure all inits")

    # Install pip deps
    run_cmd(client, "pip3 install fastapi uvicorn pyjwt bcrypt numpy jieba 2>&1 | tail -3", "pip core deps", timeout=180)
    run_cmd(client, "pip3 install mcp 2>&1 | tail -3", "pip mcp", timeout=120)

    # Kill old backend if running
    run_cmd(client, "pkill -f 'uvicorn.*main_sqlite' 2>/dev/null; sleep 1; echo killed", "kill old")

    # Start backend
    run_cmd(client, "cd ~/OrgMind && nohup python3 -m uvicorn orgmind.main_sqlite:app --host 0.0.0.0 --port 8080 > /tmp/orgmind.log 2>&1 & sleep 1; echo started", "start backend")

    time.sleep(4)

    # Verify
    out, _ = run_cmd(client, "curl -s http://127.0.0.1:8080/health", "health check")

    # Also check for errors
    run_cmd(client, "cat /tmp/orgmind.log 2>/dev/null | tail -10", "backend log")

    client.close()
except Exception as e:
    logs.append({"fatal_error": str(e)})

with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(logs, f, ensure_ascii=False, indent=2)
print("DEPLOY2_DONE")
