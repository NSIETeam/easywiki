"""EasyWiki Phase 1+2 full integration tests — outputs to file"""
import urllib.request, json, os, traceback

out = os.path.join(os.path.dirname(__file__), 'test_result.txt')
BASE = "http://127.0.0.1:8080"
passed = 0
failed = 0

def log(msg):
    with open(out, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

def req(method, path, token=None, body=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r)
        return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code

def test(name, fn):
    global passed, failed
    try:
        fn()
        log(f"[PASS] {name}")
        passed += 1
    except Exception as e:
        log(f"[FAIL] {name}: {e}")
        failed += 1

with open(out, 'w', encoding='utf-8') as f:
    f.write('=== EasyWiki Phase 1+2 Integration Tests ===\n\n')

# Login
resp, _ = req("POST", "/api/v1/auth/login", body={"email":"admin@local","password":"orgmind2026"})
token = resp["token"]
org_id = resp["user"]["org_id"]
log(f"Login OK: role={resp['user']['role']}, org={org_id}")

# Test 1: Create project
resp, code = req("POST", "/api/v1/easywiki/projects", token=token, body={"name":"TestProject"})
assert code == 200, f"Create project returned {code}: {resp}"
pid = resp["id"]
log(f"[PASS] 1. Create project: {pid}")

# Test 2: List projects
resp, code = req("GET", "/api/v1/easywiki/projects", token=token)
assert code == 200 and len(resp["projects"]) >= 1, f"List projects failed: {resp}"
log(f"[PASS] 2. List projects: {len(resp['projects'])} found")

# Test 3: Get manifest
resp, code = req("GET", f"/api/v1/easywiki/projects/{pid}/manifest", token=token)
assert code == 200 and len(resp["sections"]) == 7, f"Manifest failed: {resp}"
assert len(resp["progress_fields"]) == 5, f"Expected 5 progress fields, got {len(resp['progress_fields'])}"
log(f"[PASS] 3. Manifest: {len(resp['sections'])} sections, {len(resp['progress_fields'])} fields")

# Test 4: Create page
resp, code = req("POST", f"/api/v1/easywiki/projects/{pid}/sections/decisions_experience/pages", token=token, body={"title":"TestDecision"})
assert code == 200, f"Create page failed: {resp}"
page_id = resp["id"]
log(f"[PASS] 4. Create page: {page_id}")

# Test 5: List pages
resp, code = req("GET", f"/api/v1/easywiki/projects/{pid}/sections/decisions_experience/pages", token=token)
assert code == 200, f"List pages failed: {resp}"
log(f"[PASS] 5. List pages: {len(resp['pages'])} found")

# Test 6: Get page
resp, code = req("GET", f"/api/v1/easywiki/pages/{page_id}", token=token)
assert code == 200 and resp["title"] == "TestDecision", f"Get page failed: {resp}"
log(f"[PASS] 6. Get page: {resp['title']}")

# Test 7: Update page (PUT)
resp, code = req("PUT", f"/api/v1/easywiki/pages/{page_id}", token=token, body={"blocksuite_doc":"dGVzdA=="})
assert code == 200, f"Update page failed: {resp}"
log(f"[PASS] 7. Update page: version={resp.get('version_id','N/A')}")

# Test 8: Create pending entry
resp, code = req("POST", "/api/v1/easywiki/pending-entries", token=token, body={
    "session_id":"test-s1","project_id":pid,"tool_name":"claude-code",
    "entry_type":"decision","target_section":"decisions_experience",
    "content":"决定使用FastAPI+SQLite","file_refs":[],"confidence":0.9
})
assert code == 200 and resp["status"] == "pending", f"Pending entry failed: {resp}"
entry_id = resp["id"]
log(f"[PASS] 8. Pending entry: {entry_id} dedup={resp['dedup_hint']} pii={resp['pii_flag']}")

# Test 9: List pending
resp, code = req("GET", f"/api/v1/easywiki/projects/{pid}/pending-entries?status=pending", token=token)
assert code == 200, f"List pending failed: {resp}"
log(f"[PASS] 9. List pending: {len(resp['entries'])} found")

# Test 10: Get single pending entry
resp, code = req("GET", f"/api/v1/easywiki/pending-entries/{entry_id}", token=token)
assert code == 200 and resp["status"] == "pending", f"Get pending entry failed: {resp}"
log(f"[PASS] 10. Get pending entry: {resp['entry_type']}")

# Test 11: Approve
resp, code = req("POST", f"/api/v1/easywiki/pending-entries/{entry_id}/approve", token=token, body={})
assert code == 200 and resp["status"] == "approved", f"Approve failed: {resp}"
log(f"[PASS] 11. Approve: written_to={resp['written_to']}")

# Test 12: Verify approved removed from pending
resp, code = req("GET", f"/api/v1/easywiki/projects/{pid}/pending-entries?status=pending", token=token)
assert len(resp["entries"]) == 0, f"Still pending after approve: {len(resp['entries'])}"
log(f"[PASS] 12. Pending queue empty after approval")

# Test 13: Reject flow
resp, _ = req("POST", "/api/v1/easywiki/pending-entries", token=token, body={
    "session_id":"test-s2","project_id":pid,"tool_name":"easycode",
    "entry_type":"bug_fix","target_section":"decisions_experience",
    "content":"修复NPE问题","file_refs":[],"confidence":0.7
})
e2_id = resp["id"]
resp, code = req("POST", f"/api/v1/easywiki/pending-entries/{e2_id}/reject", token=token, body={"reason":"需要更多上下文"})
assert code == 200 and resp["status"] == "rejected", f"Reject failed: {resp}"
log(f"[PASS] 13. Reject: {e2_id}")

# Test 14: Version history
resp, code = req("GET", f"/api/v1/easywiki/versions?target_type=page&target_id={page_id}", token=token)
assert code == 200, f"Versions failed: {resp}"
log(f"[PASS] 14. Versions: {len(resp['versions'])} found")

# Test 15: Batch approve
eids = []
for i in range(3):
    resp, _ = req("POST", "/api/v1/easywiki/pending-entries", token=token, body={
        "session_id":"batch","project_id":pid,"tool_name":"claude-code",
        "entry_type":"best_practice","target_section":"decisions_experience",
        "content":f"实践#{i}","file_refs":[],"confidence":0.8
    })
    eids.append(resp["id"])
resp, code = req("POST", "/api/v1/easywiki/pending-entries/batch-approve", token=token, body={"ids":eids})
assert code == 200 and len(resp["approved"]) == 3, f"Batch approve failed: {resp}"
log(f"[PASS] 15. Batch approve: {len(resp['approved'])}/{len(eids)}")

# Test 16: Clone mount
resp, _ = req("POST", "/api/v1/easywiki/projects", token=token, body={"name":"TargetProject"})
target_pid = resp["id"]
resp, code = req("POST", f"/api/v1/easywiki/pages/{page_id}/clone-mount", token=token,
    body={"target_project_id":target_pid,"target_section":"decisions_experience"})
assert code == 200, f"Clone mount failed: {resp}"
log(f"[PASS] 16. Clone mount: {resp['cloned_page_id']}")

# Test 17: Verify cloned page appears in target project
resp, code = req("GET", f"/api/v1/easywiki/projects/{target_pid}/sections/decisions_experience/pages", token=token)
assert code == 200 and len(resp["pages"]) == 1, f"Clone verify failed: {resp}"
log(f"[PASS] 17. Clone verify: {len(resp['pages'])} pages in target")

# Test 18: Conflict listing
resp, code = req("GET", "/api/v1/easywiki/conflicts?status=open", token=token)
assert code == 200, f"Conflicts listing failed: {resp}"
log(f"[PASS] 18. Conflicts: {len(resp['conflicts'])} open")

# Test 19: Edited approve
resp, _ = req("POST", "/api/v1/easywiki/pending-entries", token=token, body={
    "session_id":"edit-test","project_id":pid,"tool_name":"claude-code",
    "entry_type":"architecture","target_section":"decisions_experience",
    "content":"原始架构说明","file_refs":[],"confidence":0.6
})
e3_id = resp["id"]
resp, code = req("POST", f"/api/v1/easywiki/pending-entries/{e3_id}/approve", token=token, body={"edited_content":"编辑后的架构说明 (人工修改版)"})
assert code == 200 and resp["status"] == "approved", f"Edited approve failed: {resp}"
log(f"[PASS] 19. Edited approve: {e3_id}")

# Summary
log(f"\n=== RESULTS: {passed} passed, {failed} failed ===")
