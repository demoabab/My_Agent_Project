import requests, getpass

BASE_URL = "http://localhost:7861"
u = input("用户名 [admin]: ").strip() or "admin"
p = getpass.getpass("密码: ").strip() or "admin"

resp = requests.post(f"{BASE_URL}/api/v1/auth/login", data={"username": u, "password": p})
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

resp = requests.post(f"{BASE_URL}/chat/kb_chat", json={
    "query": "测试", "mode": "local_kb", "kb_name": "kb",
    "top_k": 3, "score_threshold": 2.0, "return_direct": True, "stream": False,
}, headers=headers)

print("status:", resp.status_code)
print("raw[:300]:", resp.text[:300])
r = resp.json()
print("json type:", type(r).__name__)
if isinstance(r, dict):
    print("docs count:", len(r.get("docs", [])))
elif isinstance(r, str):
    import json
    r2 = json.loads(r)
    print("double-parsed type:", type(r2).__name__)
    if isinstance(r2, dict):
        print("docs count:", len(r2.get("docs", [])))
