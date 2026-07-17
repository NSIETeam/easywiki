import paramiko, os, json, time, glob

host = '60.205.220.121'
user = 'king'
password = '123456'
out_path = os.path.join(os.path.dirname(__file__), 'deploy7_log.json')
logs = []

def run(client, cmd, desc="", timeout=60):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode()
    err = stderr.read().decode()
    ec = stdout.channel.recv_exit_status()
    logs.append({"desc": desc, "out": out[:500], "err": err[:200], "exit": ec})
    return out, err, ec

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=30, allow_agent=False, look_for_keys=False)

# Create frontend dirs and upload frontend build
run(client, "mkdir -p ~/OrgMind/frontend/dist/assets", "create frontend dirs")

sftp = client.open_sftp()
local_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
frontend_dist = os.path.join(local_root, "frontend", "dist")

# Upload frontend files
for root, dirs, files in os.walk(frontend_dist):
    for f in files:
        local_path = os.path.join(root, f)
        rel_path = os.path.relpath(local_path, local_root).replace("\\", "/")
        remote_path = f"OrgMind/{rel_path}"
        try:
            sftp.put(local_path, remote_path)
            logs.append({"uploaded_frontend": rel_path})
        except Exception as e:
            logs.append({"upload_error": rel_path, "error": str(e)[:100]})
sftp.close()

# Check services __init__.py issues
run(client, "cat ~/OrgMind/orgmind/services/__init__.py 2>/dev/null | head -10", "check services init")

# Try import again
run(client, "cd ~/OrgMind && PYTHONPATH=~/OrgMind python3 -c 'from orgmind.main_sqlite import app; print(\"IMPORT_OK\")' 2>&1", "test import v3")

# Start server
run(client, "fuser -k 8080/tcp 2>/dev/null; sleep 2; echo done", "free port")
run(client, "cd ~/OrgMind && PYTHONPATH=~/OrgMind nohup python3 -m uvicorn orgmind.main_sqlite:app --host 0.0.0.0 --port 8080 > /tmp/orgmind3.log 2>&1 & sleep 4 && echo STARTED", "start server")

# Verify
run(client, "curl -s http://127.0.0.1:8080/health", "health")
run(client, "TOK=$(curl -s -X POST http://127.0.0.1:8080/api/v1/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"admin@local\",\"password\":\"orgmind2026\"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)[\"token\"])') && curl -s http://127.0.0.1:8080/api/v1/easywiki/projects -H \"Authorization: Bearer $TOK\"", "easywiki test")
run(client, "tail -5 /tmp/orgmind3.log", "log")

client.close()

with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(logs, f, ensure_ascii=False, indent=2)
print("DONE")
