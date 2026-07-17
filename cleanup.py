import paramiko, os, json

host = '60.205.220.121'
user = 'king'
password = '123456'
out_path = os.path.join(os.path.dirname(__file__), 'cleanup_log.json')
logs = []

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=30, allow_agent=False, look_for_keys=False)

def run(cmd, desc=""):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
    out = stdout.read().decode()
    err = stderr.read().decode()
    ec = stdout.channel.recv_exit_status()
    logs.append({"desc": desc, "out": out[:300], "err": err[:200], "exit": ec})
    return out

# Kill server
run("fuser -k 8080/tcp 2>/dev/null; pkill -f 'uvicorn.*main_sqlite' 2>/dev/null; echo done", "kill server")

# Remove OrgMind directory
run("rm -rf ~/OrgMind ~/frontend_dist.tar.gz && echo removed", "remove project")

# Remove start script
run("rm -f /tmp/start_orgmind.sh /tmp/orgmind*.log && echo cleaned", "clean temp")

# Verify
run("ls ~/OrgMind 2>&1 || echo 'CLEAN'", "verify removed")

client.close()

with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(logs, f, ensure_ascii=False, indent=2)
print("CLEANUP_DONE")
