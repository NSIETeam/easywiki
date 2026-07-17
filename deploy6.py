import paramiko, os, json, time

host = '60.205.220.121'
user = 'king'
password = '123456'
out_path = os.path.join(os.path.dirname(__file__), 'deploy6_log.json')
logs = []

def run(client, cmd, desc="", timeout=60):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode()
    err = stderr.read().decode()
    ec = stdout.channel.recv_exit_status()
    logs.append({"desc": desc, "out": out[:600], "err": err[:300], "exit": ec})
    return out, err, ec

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=30, allow_agent=False, look_for_keys=False)

# Upload missing files
sftp = client.open_sftp()
local_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
missing_files = [
    "orgmind/governance/validators.py",
    "orgmind/governance/__init__.py",
    "orgmind/services/__init__.py",
]
for f in missing_files:
    local_path = os.path.join(local_root, f)
    if os.path.exists(local_path):
        sftp.put(local_path, f"OrgMind/{f}")
        logs.append({"uploaded": f})
sftp.close()

# Test import now
run(client, "cd ~/OrgMind && PYTHONPATH=~/OrgMind python3 -c 'from orgmind.main_sqlite import app; print(\"IMPORT_OK\")' 2>&1", "test import v2")

# Kill old server + restart
run(client, "fuser -k 8080/tcp 2>/dev/null; sleep 2; echo done", "free port")
run(client, "cd ~/OrgMind && PYTHONPATH=~/OrgMind nohup python3 -m uvicorn orgmind.main_sqlite:app --host 0.0.0.0 --port 8080 > /tmp/orgmind2.log 2>&1 & sleep 4 && echo STARTED", "start server")

# Test health
run(client, "curl -s http://127.0.0.1:8080/health 2>&1 || echo DEAD", "health")

# Test EasyWiki endpoints
run(client, "curl -s -X POST http://127.0.0.1:8080/api/v1/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"admin@local\",\"password\":\"orgmind2026\"}' | python3 -c 'import sys,json;d=json.load(sys.stdin);print(\"LOGIN:\",d.get(\"user\",{}).get(\"role\",\"FAIL\"))' 2>&1", "login")
run(client, "TOK=$(curl -s -X POST http://127.0.0.1:8080/api/v1/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"admin@local\",\"password\":\"orgmind2026\"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)[\"token\"])') && curl -s http://127.0.0.1:8080/api/v1/easywiki/projects -H \"Authorization: Bearer $TOK\"", "easywiki projects")

run(client, "tail -10 /tmp/orgmind2.log 2>/dev/null", "log")

client.close()

with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(logs, f, ensure_ascii=False, indent=2)
print("DONE")
