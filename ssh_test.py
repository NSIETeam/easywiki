import paramiko, os, json

host = '60.205.220.121'
user = 'king'
password = '123456'
out_path = os.path.join(os.path.dirname(__file__), 'ssh_test.json')

result = {}
try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=30, allow_agent=False, look_for_keys=False)

    stdin, stdout, stderr = client.exec_command(
        'echo "===CONNECTED===" && uname -a && '
        'echo "===OS===" && cat /etc/os-release 2>/dev/null | head -3 && '
        'echo "===DISK===" && df -h / | tail -1 && '
        'echo "===MEM===" && free -h 2>/dev/null | head -2 || free -m 2>/dev/null | head -2 && '
        'echo "===PYTHON===" && which python3 python 2>/dev/null || echo "no python in PATH" && '
        'python3 --version 2>/dev/null && '
        'echo "===NODE===" && which node npm 2>/dev/null || echo "no node in PATH" && '
        'node --version 2>/dev/null && '
        'echo "===HOME===" && ls ~/ 2>/dev/null | head -20'
    )
    output = stdout.read().decode()
    err = stderr.read().decode()
    result['status'] = 'ok'
    result['output'] = output
    result['stderr'] = err
    client.close()
except Exception as e:
    result['status'] = 'failed'
    result['error'] = str(e)

with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print("DONE")
