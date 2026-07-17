import paramiko, os, json, time

host = '60.205.220.121'
user = 'king'
password = '123456'
out_path = os.path.join(os.path.dirname(__file__), 'deploy5_log.json')
logs = []

def run(client, cmd, desc="", timeout=60):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode()
    err = stderr.read().decode()
    ec = stdout.channel.recv_exit_status()
    logs.append({"desc": desc, "out": out[:800], "err": err[:300], "exit": ec})
    return out, err, ec

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=30, allow_agent=False, look_for_keys=False)

# Fix: need PYTHONPATH set correctly
# Also need to install additional deps (openai, mcp)
run(client, "pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple openai httpx 2>&1 | tail -3", "pip openai")
run(client, "pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple mcp 2>&1 | tail -3", "pip mcp")

# Test import with PYTHONPATH
run(client, "cd ~/OrgMind && PYTHONPATH=~/OrgMind python3 -c 'from orgmind.main_sqlite import app; print(\"IMPORT_OK\")' 2>&1", "test import with PYTHONPATH")

# Kill everything on port 8080
run(client, "fuser -k 8080/tcp 2>/dev/null; sleep 1; echo done", "free port 8080")

# Start with correct PYTHONPATH
run(client, "cd ~/OrgMind && PYTHONPATH=~/OrgMind nohup python3 -m uvicorn orgmind.main_sqlite:app --host 0.0.0.0 --port 8080 > /tmp/orgmind.log 2>&1 & sleep 4 && echo 'STARTED'", "start with PYTHONPATH")

# Check
run(client, "curl -s http://127.0.0.1:8080/health", "health check")
run(client, "tail -20 /tmp/orgmind.log", "log tail")

# Login + EasyWiki test
run(client, "export PYTHONPATH=~/OrgMind && TOKEN=$(python3 -c \"import urllib.request,json; r=urllib.request.Request('http://127.0.0.1:8080/api/v1/auth/login',data=json.dumps({'email':'admin@local','password':'orgmind2026'}).encode(),headers={'Content-Type':'application/json'},method='POST'); d=json.loads(urllib.request.urlopen(r).read()); print(d['token'])\") && echo TOKEN_OK && curl -s 'http://127.0.0.1:8080/api/v1/easywiki/projects' -H \"Authorization: Bearer $TOKEN\"", "easywiki test")

client.close()

with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(logs, f, ensure_ascii=False, indent=2)
print("DONE")
