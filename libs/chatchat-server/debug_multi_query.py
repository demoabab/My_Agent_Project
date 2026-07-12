"""
知识库诊断 + MultiQuery 调试脚本 (支持多租户认证)
用法: python debug_multi_query.py
"""
from __future__ import annotations

import json
import time
import requests
import getpass

BASE_URL = "http://localhost:7861"
TOKEN = None


def login():
    global TOKEN
    print("=" * 60)
    print("认证登录")
    print("=" * 60)

    username = input("用户名: ").strip() or "admin"
    password = getpass.getpass("密码: ").strip() or "admin"

    resp = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    if resp.status_code != 200:
        print(f"登录失败: {resp.status_code} {resp.text}")
        return False

    data = resp.json()
    TOKEN = data.get("access_token")
    if not TOKEN:
        print(f"未获取到 token: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return False

    print(f"登录成功!")
    print(f"  用户名: {data.get('username', '?')}")
    print(f"  user_id: {data.get('user_id', '?')}")

    tenants = data.get("tenants", [])
    if tenants:
        print(f"  所属租户 ({len(tenants)} 个):")
        for t in tenants:
            print(f"    - {t.get('tenant_name', t.get('tenant_id', '?'))} (id={t.get('tenant_id', '?')})")
    else:
        print(f"  租户: 无")

    return True


def headers():
    return {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}


def api_get(path, **kwargs):
    resp = requests.get(f"{BASE_URL}{path}", headers=headers(), **kwargs)
    return resp


def api_post(path, **kwargs):
    resp = requests.post(f"{BASE_URL}{path}", headers=headers(), **kwargs)
    return resp


def main():
    if not login():
        print("无法登录，请检查服务是否启动以及用户名密码是否正确")
        print("默认账号: admin / admin")
        return

    print()
    print("=" * 60)
    print("1. 列出你的所有知识库")
    print("=" * 60)

    resp = api_get("/knowledge_base/list_knowledge_bases")
    print(f"HTTP {resp.status_code}")

    if resp.status_code == 200:
        data = resp.json()
        kbs = data.get("data", [])
        if kbs:
            print(f"共 {len(kbs)} 个知识库:")
            for kb in kbs:
                print(f"  - {kb}")
        else:
            print("没有知识库！需要先创建。")
            print()
            print("创建知识库命令:")
            print(f'  POST {BASE_URL}/knowledge_base/create_kb')
            print(f'  参数: knowledge_base_name, vector_store_type (默认faiss), kb_info')
            print()
            print("或者用 curl:")
            print(f'  curl -X POST {BASE_URL}/knowledge_base/create_kb \\')
            print(f'    -H "Authorization: Bearer {TOKEN}" \\')
            print(f'    -F "knowledge_base_name=my_kb" \\')
            print(f'    -F "vector_store_type=faiss" \\')
            print(f'    -F "kb_info=我的知识库"')
            return
    else:
        print(f"响应: {resp.text[:500]}")
        return

    # 选择知识库
    kb_name = input(f"\n输入要测试的知识库名称: ").strip()
    if not kb_name:
        kb_name = kbs[0] if isinstance(kbs[0], str) else kbs[0].get("kb_name", "samples")
        print(f"使用默认: {kb_name}")

    print()
    print("=" * 60)
    print("2. 查看知识库文件")
    print("=" * 60)

    resp = api_get("/knowledge_base/list_files", params={"knowledge_base_name": kb_name})
    if resp.status_code == 200:
        data = resp.json()
        files = data.get("data", [])
        print(f"{kb_name} 知识库文件数: {len(files)}")
        for f in files[:10]:
            if isinstance(f, dict):
                print(f"  - {f.get('file_name', f.get('name', str(f)))}")
            else:
                print(f"  - {f}")
        if len(files) == 0:
            print()
            print("⚠️  该知识库为空！上传文档示例:")
            print(f'  curl -X POST {BASE_URL}/knowledge_base/upload_docs \\')
            print(f'    -H "Authorization: Bearer {TOKEN}" \\')
            print(f'    -F "knowledge_base_name={kb_name}" \\')
            print(f'    -F "files=@/path/to/your/document.txt"')
            return
    else:
        print(f"响应: {resp.text[:500]}")
        return

    print()
    print("=" * 60)
    print("3. 基准检索测试 (score_threshold=2.0)")
    print("=" * 60)

    payload = {
        "query": "测试",
        "mode": "local_kb",
        "kb_name": kb_name,
        "top_k": 10,
        "score_threshold": 2.0,
        "return_direct": True,
        "stream": False,
    }
    resp = api_post("/chat/kb_chat", json=payload)
    if resp.status_code != 200:
        print(f"失败: {resp.status_code} {resp.text[:300]}")
        return

    data = resp.json()
    if isinstance(data, str):
        data = json.loads(data)
    doc_count = len(data.get("docs", []))
    print(f"score_threshold=2.0, top_k=10 → 返回 {doc_count} 条文档")
    if doc_count > 0:
        first = data["docs"][0]
        if isinstance(first, dict):
            print(f"  首条预览: {first.get('page_content', str(first))[:150]}...")
        else:
            print(f"  首条: {str(first)[:150]}...")

    print()
    print("=" * 60)
    print("4. MultiQuery vs 普通检索 对比")
    print("=" * 60)

    test_query = input("输入测试查询 (回车使用默认): ").strip()
    test_query = test_query or "怎样提高检索匹配的准确度"

    def do_search(multi_query: bool):
        t0 = time.perf_counter()
        resp = api_post("/chat/kb_chat", json={
            "query": test_query,
            "mode": "local_kb",
            "kb_name": kb_name,
            "top_k": 5,
            "score_threshold": 0.5,  # 有筛选才有差异：得分低于0.5的文档被丢弃
            "multi_query": multi_query,
            "return_direct": True,
            "stream": False,
        })
        elapsed = time.perf_counter() - t0
        data = resp.json()
        if isinstance(data, str):
            data = json.loads(data)
        docs = data.get("docs", [])
        return elapsed, docs

    t_normal, normal_docs = do_search(False)
    t_mq, mq_docs = do_search(True)

    print(f"\n{'指标':<20} {'普通检索':>20} {'多查询检索':>20}")
    print(f"{'─' * 60}")
    print(f"{'耗时 (秒)':<20} {t_normal:>20.2f} {t_mq:>20.2f}")
    print(f"{'返回文档数':<20} {len(normal_docs):>20} {len(mq_docs):>20}")

    # 对比文档内容
    def get_doc_key(doc):
        if isinstance(doc, str):
            doc = json.loads(doc) if doc.startswith("{") else {"page_content": doc}
        return doc.get("page_content", str(doc))[:80]

    normal_keys = {get_doc_key(d) for d in normal_docs}
    mq_keys = {get_doc_key(d) for d in mq_docs}
    shared = normal_keys & mq_keys
    normal_only = normal_keys - mq_keys
    mq_only = mq_keys - normal_keys

    print(f"\n{'─' * 60}")
    print(f"去重后的文档对比 (按内容前80字符)")
    print(f"{'─' * 60}")
    print(f"  两者共有: {len(shared)} 篇")
    print(f"  仅普通检索命中: {len(normal_only)} 篇")
    print(f"  仅多查询检索命中: {len(mq_only)} 篇 ← 这就是多查询提升的召回")

    if mq_only:
        print(f"\n多查询独有的文档:")
        for i, doc in enumerate(mq_only, 1):
            print(f"  [{i}] {doc[:120]}...")

    if normal_only:
        print(f"\n普通检索独有的文档 (多查询丢失):")
        for i, doc in enumerate(normal_only, 1):
            print(f"  [{i}] {doc[:120]}...")

    if not mq_only and not normal_only:
        print(f"\n文档内容完全一致 — 建议换个查询词试试")
        print(f"推荐查询: '怎样提高检索匹配的准确度'")
        print(f"  (文档里写的是'召回率''相似度''语义匹配'等不同表述)")


if __name__ == "__main__":
    main()
