import paramiko, os, json, time, tarfile, io

host = '60.205.220.121'
user = 'king'
password = '123456'
out_path = os.path.join(os.path.dirname(__file__), 'deploy8_log.json')
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
client.connect(host, username=user, password=password, timeout=60, allow_agent=False, look_for_keys=False)

# Quick fix: just create empty assets dir to bypass the StaticFiles error
# Then we can upload the real frontend later
run(client, "mkdir -p ~/OrgMind/frontend/dist/assets && touch ~/OrgMind/frontend/dist/index.html", "create frontend dirs")

# Also fix: the services/__init__.py was overwritten by touch.
# main_sqlite.py imports directly from submodules, not from services package, so empty __init__ is fine.
# But governance/__init__.py needs validators. Already uploaded.
# Check if there are other missing init files causing issues.

# Test import
out, err, ec = run(client, "cd ~/OrgMind && PYTHONPATH=~/OrgMind python3 -c 'from orgmind.main_sqlite import app; print(\"IMPORT_OK\")' 2>&1", "test import v4")

if "IMPORT_OK" in out:
    # Start server
    run(client, "fuser -k 8080/tcp 2>/dev/null; sleep 1", "free port")
    run(client, "cd ~/OrgMind && PYTHONPATH=~/OrgMind nohup python3 -m uvicorn orgmind.main_sqlite:app --host 0.0.0.0 --port 8080 > /tmp/orgmind4.log 2>&1 & sleep 5 && echo 'STARTED'", "start")

    time.sleep(2)
    run(client, "curl -s http://127.0.0.1:8080/health", "health")

    # Now upload the real frontend as a tar.gz
    # Create tar.gz locally
    local_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    frontend_dist = os.path.join(local_root, "frontend", "dist")
    tar_path = os.path.join(local_root, "frontend_dist.tar.gz")

    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(frontend_dist, arcname="dist")

    # Upload tar
    sftp = client.open_sftp()
    sftp.put(tar_path, "OrgMind/frontend_dist.tar.gz")
    sftp.close()

    # Extract on server
    run(client, "cd ~/OrgMind/frontend && tar xzf ../frontend_dist.tar.gz && ls dist/", "extract frontend")

    # Verify SPA works
    run(client, "curl -s http://127.0.0.1:8080/ | head -5", "spa check")

    # Full EasyWiki test
    run(client, "TOK=$(curl -s -X POST http://127.0.0.1:8080/api/v1/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"admin@local\",\"password\":\"orgmind2026\"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)[\"token\"])') && echo TOKEN_OK && curl -s -X POST http://127.0.0.1:8080/api/v1/easywiki/projects -H 'Content-Type: application/json' -H \"Authorization: Bearer $TOK\" -d '{\"name\":\"ServerDeployTest\"}'", "create project")
else:
    logs.append({"import_failed": True, "output": out[:1000]})

client.close()

with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(logs, f, ensure_ascii=False, indent=2)
print("DONE")
