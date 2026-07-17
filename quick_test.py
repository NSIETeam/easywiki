import sys, urllib.request, json, os

output_path = os.path.join(os.path.dirname(__file__), 'quick_test_result.txt')
with open(output_path, 'w') as f:
    f.write('START\n')
    f.flush()
    try:
        data = json.dumps({'email':'admin@local','password':'orgmind2026'}).encode()
        req = urllib.request.Request('http://127.0.0.1:8080/api/v1/auth/login', data=data, headers={'Content-Type':'application/json'}, method='POST')
        resp = urllib.request.urlopen(req)
        body = json.loads(resp.read())
        token = body['token']
        f.write(f'LOGIN OK\n')
        f.flush()

        data = json.dumps({'name':'QuickTest'}).encode()
        req = urllib.request.Request('http://127.0.0.1:8080/api/v1/easywiki/projects', data=data, headers={'Authorization':f'Bearer {token}','Content-Type':'application/json'}, method='POST')
        resp = urllib.request.urlopen(req)
        body = json.loads(resp.read())
        f.write(f'CREATE OK: {body}\n')
        f.flush()
    except Exception as e:
        import traceback
        f.write(f'ERROR: {e}\n{traceback.format_exc()}\n')
        f.flush()
