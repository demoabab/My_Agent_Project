"""上传测试文档到知识库"""
import requests
import getpass
from pathlib import Path

BASE_URL = "http://localhost:7861"
DOCS_DIR = Path("../../chatchat_data/test_docs")

username = input("用户名 [admin]: ").strip() or "admin"
password = getpass.getpass("密码: ").strip() or "admin"

# 登录
resp = requests.post(f"{BASE_URL}/api/v1/auth/login", data={"username": username, "password": password})
if resp.status_code != 200:
    print(f"登录失败: {resp.text}")
    exit(1)

data = resp.json()
token = data["access_token"]
print(f"登录成功: {data['username']}")

kb_name = input("知识库名称 [kb]: ").strip() or "kb"
headers = {"Authorization": f"Bearer {token}"}

files = sorted(DOCS_DIR.glob("*.md"))
print(f"共 {len(files)} 个文档待上传到 '{kb_name}'\n")

for i, f in enumerate(files, 1):
    print(f"[{i}/{len(files)}] 上传: {f.name} ...", end=" ")
    with open(f, "rb") as fh:
        resp = requests.post(
            f"{BASE_URL}/knowledge_base/upload_docs",
            headers=headers,
            data={"knowledge_base_name": kb_name},
            files={"files": (f.name, fh, "text/markdown")},
        )
    if resp.status_code == 200:
        print("OK")
    else:
        print(f"失败 ({resp.status_code}): {resp.text[:100]}")

print(f"\n上传完成!")
