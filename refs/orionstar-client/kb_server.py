#!/usr/bin/env python3
"""OrionStar 销售知识库 - 带账号权限管理的后端服务器"""
import http.server
import json
import os
import hashlib
import secrets
import urllib.parse
import urllib.request
import time

PORT = 8080
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(DATA_DIR, 'kb_users.json')
SESSIONS = {}  # token -> {user, expiry}

# ====== 默认用户 ======
DEFAULT_USERS = {
    "wangmeng12@cmcm.com": {
        "password": "adgjm123ptw",
        "name": "王蒙",
        "role": "admin",
        "permissions": ["domestic:read","domestic:write","overseas:read","overseas:write","admin"],
        "created_at": time.time()
    },
    "demo": {
        "password": "demo2026",
        "name": "演示账号",
        "role": "viewer",
        "permissions": ["domestic:read","overseas:read"],
        "created_at": time.time()
    }
}

# ====== 加载/初始化用户 ======
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

users = load_users()
if not users:
    users = DEFAULT_USERS
    save_users(users)

# ====== 请求处理 ======
class KBHandler(http.server.BaseHTTPRequestHandler):
    def _json(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def _html(self, content, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(content.encode())

    def _serve_file(self, path):
        filepath = os.path.join(DATA_DIR, path.lstrip('/'))
        if not os.path.exists(filepath) or not os.path.isfile(filepath):
            self._json({'error':'not found'}, 404)
            return
        ext = os.path.splitext(filepath)[1]
        types = {'.html':'text/html','.css':'text/css','.js':'application/javascript',
                 '.png':'image/png','.jpg':'image/jpeg','.webp':'image/webp','.svg':'image/svg+xml'}
        ct = types.get(ext, 'application/octet-stream')
        with open(filepath, 'rb') as f:
            data = f.read()
        self.send_response(200)
        self.send_header('Content-Type', ct)
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(data)

    def _get_body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length == 0: return {}
        return json.loads(self.rfile.read(length))

    def _check_auth(self):
        auth = self.headers.get('Authorization', '')
        token = auth.replace('Bearer ', '')
        session = SESSIONS.get(token)
        if not session or session['expiry'] < time.time():
            return None
        return session

    def _handle_me(self):
        session = self._check_auth()
        if not session:
            self._json({'ok':False,'error':'未登录'}, 401)
            return
        email = session['user']
        user = users.get(email)
        if not user:
            self._json({'ok':False,'error':'用户不存在'}, 401)
            return
        self._json({'ok':True,'user':{
            'email':email,'name':user['name'],'role':user['role'],
            'permissions':user['permissions']
        }})

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path

        if path == '/api/login':
            body = self._get_body()
            email = body.get('email', '')
            pwd = body.get('password', '')
            user = users.get(email)
            if not user or user['password'] != pwd:
                self._json({'ok':False,'error':'账号或密码错误'}, 401)
                return
            token = secrets.token_hex(32)
            SESSIONS[token] = {'user': email, 'expiry': time.time() + 86400}
            self._json({'ok':True,'token':token,'user':{
                'email':email,'name':user['name'],'role':user['role'],
                'permissions':user['permissions']
            }})

        elif path == '/api/logout':
            token = self.headers.get('Authorization','').replace('Bearer ','')
            SESSIONS.pop(token, None)
            self._json({'ok':True})

        elif path == '/api/me':
            self._handle_me()

        elif path == '/api/users':
            session = self._check_auth()
            if not session:
                self._json({'ok':False,'error':'未登录'}, 401)
                return
            email = session['user']
            user = users.get(email)
            if not user or 'admin' not in user.get('permissions',[]):
                self._json({'ok':False,'error':'无权限'}, 403)
                return
            body = self._get_body()
            action = body.get('action','')
            if action == 'list':
                user_list = [{'email':k,'name':v['name'],'role':v['role'],
                             'permissions':v['permissions'],'created_at':v.get('created_at','')}
                            for k,v in users.items()]
                self._json({'ok':True,'users':user_list})
            elif action == 'create':
                new_email = body.get('email','')
                new_name = body.get('name','')
                new_pwd = body.get('password','')
                new_role = body.get('role','viewer')
                new_perms = body.get('permissions',['domestic:read','overseas:read'])
                if new_email in users:
                    self._json({'ok':False,'error':'账号已存在'}, 400)
                    return
                users[new_email] = {
                    'password': new_pwd, 'name': new_name, 'role': new_role,
                    'permissions': new_perms, 'created_at': time.time()
                }
                save_users(users)
                self._json({'ok':True})
            elif action == 'delete':
                del_email = body.get('email','')
                if del_email in users:
                    del users[del_email]
                    save_users(users)
                self._json({'ok':True})
            elif action == 'update':
                upd_email = body.get('email','')
                if upd_email in users:
                    if 'password' in body:
                        users[upd_email]['password'] = body['password']
                    if 'permissions' in body:
                        users[upd_email]['permissions'] = body['permissions']
                    if 'role' in body:
                        users[upd_email]['role'] = body['role']
                    if 'name' in body:
                        users[upd_email]['name'] = body['name']
                    save_users(users)
                self._json({'ok':True})
            else:
                self._json({'ok':False,'error':'unknown action'}, 400)

        elif path == '/api/generate':
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            model = body.get('model', 'kimi-k3')
            prompt = body.get('prompt', '')
            req = urllib.request.Request(
                'https://easyrouter.cmcm.com/v1/chat/completions',
                data=json.dumps({
                    'model': model,
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_tokens': 4000
                }).encode(),
                headers={
                    'Authorization': 'Bearer sk-AKaZUBbgRCr4xPdzJnOo8ULoAFyc3loH816qDnyuGc2Ikur0',
                    'Content-Type': 'application/json'
                }
            )
            try:
                resp = urllib.request.urlopen(req, timeout=180)
                result = json.loads(resp.read())
                self._json({'ok': True, 'content': result['choices'][0]['message']['content']})
            except Exception as e:
                self._json({'ok': False, 'error': str(e)}, 500)

        else:
            self._json({'ok':False,'error':'not found'}, 404)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path == '/' or path == '/index.html':
            self._serve_file('/orionstar-kb.html')
        elif path.startswith('/orionstar-images/'):
            self._serve_file(path)
        elif path == '/api/check':
            self._json({'ok':True,'server':'running'})
        elif path == '/api/me':
            self._handle_me()
        elif path == '/orionstar-kb.html':
            self._serve_file(path)
        else:
            self._json({'ok':False,'error':'not found'}, 404)

    def log_message(self, fmt, *args):
        print(f"[KB] {args[0]} {args[1]}", flush=True)

if __name__ == '__main__':
    server = http.server.HTTPServer(('0.0.0.0', PORT), KBHandler)
    print(f"🚀 OrionStar KB Server running on http://localhost:{PORT}", flush=True)
    print(f"   👤 账号: wangmeng12@cmcm.com / adgjm123ptw (管理员)", flush=True)
    print(f"   👤 账号: demo / demo2026 (只读查看者)", flush=True)
    server.serve_forever()
