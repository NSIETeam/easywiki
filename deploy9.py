import paramiko, os, json, time, tarfile

host = '60.205.220.121'
user = 'king'
password = '123456'
out_path = os.path.join(os.path.dirname(__file__), 'deploy9_log.json')
logs = []

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=60, allow_agent=False, look_for_keys=False)

def run(cmd, desc="", timeout=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode()
    err = stderr.read().decode()
    ec = stdout.channel.recv_exit_status()
    logs.append({"desc": desc, "out": out[:500], "err": err[:200], "exit": ec})
    return out, err

# Step 1: Create assets dir (critical fix)
run("mkdir -p ~/OrgMind/frontend/dist/assets && touch ~/OrgMind/frontend/dist/index.html", "create dirs")
run("ls ~/OrgMind/frontend/dist/", "verify dirs")

# Step 2: Test import
out, _ = run("cd ~/OrgMind && PYTHONPATH=~/OrgMind timeout 15 python3 -c 'from orgmind.main_sqlite import app; print(\"IMPORT_OK\")' 2>&1", "test import")

if "IMPORT_OK" in out:
    # Step 3: Kill old and start fresh
    run("fuser -k 8080/tcp 2>/dev/null || true; sleep 1; echo done", "free port")

    # Use a startup script approach to properly daemonize
    run("cat > /tmp/start_orgmind.sh << 'EOF'\n#!/bin/bash\ncd ~/OrgMind\nexport PYTHONPATH=~/OrgMind\npython3 -m uvicorn orgmind.main_sqlite:app --host 0.0.0.0 --port 8080\nEOF\nchmod +x /tmp/start_orgmind.sh", "create start script")

    # Start daemon using setsid to fully detach
    run("setsid /tmp/start_orgmind.sh > /tmp/orgmind.log 2>&1 < /dev/null &", "start daemon")

    time.sleep(5)

    # Step 4: Verify
    run("curl -s http://127.0.0.1:8080/health", "health check")

    # Step 5: Login + EasyWiki test
    run("TOK=$(curl -s -X POST http://127.0.0.1:8080/api/v1/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"admin@local\",\"password\":\"orgmind2026\"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)[\"token\"])') && echo \"TOKEN_OK\" && curl -s -X POST http://127.0.0.1:8080/api/v1/easywiki/projects -H 'Content-Type: application/json' -H \"Authorization: Bearer $TOK\" -d '{\"name\":\"ServerProject\"}'", "easywiki test")

    # Step 6: Check server log for errors
    run("tail -15 /tmp/orgmind.log 2>/dev/null || echo no_log", "server log")

    # Step 7: Upload frontend as tar.gz
    local_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    tar_path = os.path.join(local_root, "frontend_dist.tar.gz")
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(os.path.join(local_root, "frontend", "dist"), arcname="dist")

    sftp = client.open_sftp()
    sftp.put(tar_path, "OrgMind/frontend_dist.tar.gz")
    sftp.close()
    logs.append({"step": "uploaded tar.gz"})

    run("cd ~/OrgMind/frontend && rm -rf dist && tar xzf ../frontend_dist.tar.gz && ls dist/", "extract frontend")
    run("curl -s http://127.0.0.1:8080/ | head -3", "spa check")
else:
    logs.append({"import_failed": out})

client.close()

with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(logs, f, ensure_ascii=False, indent=2)
print("DONE")
