import paramiko, os, json, time

host = '60.205.220.121'
user = 'king'
password = '123456'
out_path = os.path.join(os.path.dirname(__file__), 'deploy3_log.json')
logs = []

def run(client, cmd, desc="", timeout=120):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode()
    err = stderr.read().decode()
    ec = stdout.channel.recv_exit_status()
    logs.append({"desc": desc, "out": out[:500], "err": err[:200], "exit": ec})
    return out, err, ec

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=30, allow_agent=False, look_for_keys=False)

# Step 1: Check current state
run(client, "ls ~/OrgMind/orgmind/main_sqlite.py 2>/dev/null && echo FOUND || echo MISSING", "check files")
run(client, "ps aux | grep uvicorn | grep -v grep", "check uvicorn")
run(client, "pip3 list 2>/dev/null | grep -i fastapi", "check fastapi")

# Step 2: Install deps
run(client, "pip3 install --user fastapi uvicorn pyjwt bcrypt numpy 2>&1 | tail -5", "pip install deps", timeout=180)

# Step 3: Verify install
run(client, "python3 -c 'import fastapi; print(\"fastapi ok\")' 2>&1", "verify fastapi")
run(client, "python3 -c 'import jwt; print(\"pyjwt ok\")' 2>&1", "verify pyjwt")

# Step 4: Kill old + start fresh
run(client, "pkill -f uvicorn 2>/dev/null; sleep 2; echo done", "kill uvicorn")
run(client, "cd ~/OrgMind && nohup python3 -m uvicorn orgmind.main_sqlite:app --host 0.0.0.0 --port 8080 > /tmp/orgmind.log 2>&1 & sleep 3 && echo 'started'", "start server")
run(client, "sleep 2 && curl -s http://127.0.0.1:8080/health", "health check")
run(client, "tail -20 /tmp/orgmind.log 2>/dev/null", "log check")

# Step 5: Test EasyWiki endpoints
run(client, "curl -s -X POST http://127.0.0.1:8080/api/v1/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"admin@local\",\"password\":\"orgmind2026\"}' | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get(\"user\",{}).get(\"role\",\"NO_TOKEN\"))' 2>&1", "login test")
run(client, "TOKEN=$(curl -s -X POST http://127.0.0.1:8080/api/v1/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"admin@local\",\"password\":\"orgmind2026\"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)[\"token\"])') && curl -s http://127.0.0.1:8080/api/v1/easywiki/projects -H \"Authorization: Bearer $TOKEN\"", "easywiki test")

client.close()

with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(logs, f, ensure_ascii=False, indent=2)
print("DONE")
