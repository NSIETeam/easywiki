import paramiko, os, json, time

host = '60.205.220.121'
user = 'king'
password = '123456'
out_path = os.path.join(os.path.dirname(__file__), 'deploy4_log.json')
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

# Quick check of what's installed
run(client, "python3 -c 'import fastapi; print(\"fastapi:\",fastapi.__version__)' 2>&1", "check fastapi")
run(client, "python3 -c 'import uvicorn; print(\"uvicorn ok\")' 2>&1", "check uvicorn")
run(client, "python3 -c 'import jwt; print(\"pyjwt ok\")' 2>&1", "check pyjwt")
run(client, "python3 -c 'import bcrypt; print(\"bcrypt ok\")' 2>&1", "check bcrypt")
run(client, "python3 -c 'import numpy; print(\"numpy ok\")' 2>&1", "check numpy")
run(client, "python3 -c 'import jieba; print(\"jieba ok\")' 2>&1", "check jieba")

# Attempt quick startup to see what modules are missing
run(client, "pkill -f uvicorn 2>/dev/null; sleep 1; echo done", "kill old")
run(client, "cd ~/OrgMind && timeout 10 python3 -c 'from orgmind.main_sqlite import app; print(\"IMPORT_OK\")' 2>&1", "test import")

# Install missing deps in background, use pip with Tuna mirror for speed
run(client, "pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple fastapi uvicorn pyjwt bcrypt numpy jieba 2>&1 | tail -10", "pip install with tsinghua mirror", timeout=180)

# Verify after install
run(client, "python3 -c 'from orgmind.main_sqlite import app; print(\"IMPORT_OK\")' 2>&1", "verify import after install")

# Start server
run(client, "cd ~/OrgMind && nohup python3 -m uvicorn orgmind.main_sqlite:app --host 0.0.0.0 --port 8080 > /tmp/orgmind.log 2>&1 & sleep 3 && echo 'SERVER_STARTED'", "start server")
time.sleep(3)

# Check health
run(client, "curl -s http://127.0.0.1:8080/health 2>&1 || echo 'NOT_RUNNING'", "health check")
run(client, "tail -15 /tmp/orgmind.log 2>/dev/null", "server log")

client.close()

with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(logs, f, ensure_ascii=False, indent=2)
print("DONE")
