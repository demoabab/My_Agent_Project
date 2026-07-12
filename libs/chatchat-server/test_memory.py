"""长期记忆功能验证脚本
用法: python test_memory.py

前提: 服务端已重启，数据库迁移已执行
"""
from __future__ import annotations

import json
import time
import sqlite3
import requests
import getpass
from pathlib import Path

BASE_URL = "http://localhost:7861"
# 数据库路径（与 basic_settings.yaml 中 CHATCHAT_ROOT 一致）
DB_PATH = "D:/Langchain_Chatchat_master/chatchat_data/data/knowledge_base/info.db"


def parse_content(r: dict) -> str:
    """兼容 OpenAIChatOutput 的嵌套响应格式"""
    if isinstance(r, str):
        r = json.loads(r)
    # 直接取顶层 content
    content = r.get("content")
    if content:
        return content
    # 从 choices 嵌套中提取
    choices = r.get("choices", [])
    if choices:
        inner = choices[0].get("message") or choices[0].get("delta") or {}
        return inner.get("content", "") or str(r)[:300]
    return str(r)[:300]


def main():
    print("=" * 60)
    print("长期记忆系统验证")
    print("=" * 60)

    # 登录
    username = input("用户名 [admin]: ").strip() or "admin"
    password = getpass.getpass("密码: ").strip() or "admin"
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", data={"username": username, "password": password})
    if resp.status_code != 200:
        print(f"登录失败: {resp.text}")
        return
    data = resp.json()
    token = data["access_token"]
    user_id = data["user_id"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"登录: {data['username']} (user_id={user_id[:8]}...)")
    print(f"租户: {[t.get('tenant_name', t.get('tenant_id', '?')) for t in data.get('tenants', [])]}")

    kb_name = input("知识库名称 [kb]: ").strip() or "kb"

    print()
    print("=" * 60)
    print("第1步: 自我介绍对话（播种记忆）")
    print("=" * 60)

    query1 = "你好，我叫张三，是一名Python后端开发工程师。我喜欢简洁的代码风格，回答时请给我代码示例。我正在优化一个知识库问答系统。"

    print(f"用户: {query1}")
    resp = requests.post(f"{BASE_URL}/chat/kb_chat", json={
        "query": query1,
        "mode": "local_kb",
        "kb_name": kb_name,
        "stream": False,
    }, headers=headers)
    if resp.status_code == 200:
        r = resp.json()
        content = parse_content(r)
        print(f"AI: {content[:300]}...")
    else:
        print(f"请求失败: {resp.status_code}")
        print(f"响应: {resp.text[:300]}")
        return

    print()
    print("等待异步记忆提取完成...")
    time.sleep(3)

    print()
    print("=" * 60)
    print("第2步: 检查数据库中的记忆")
    print("=" * 60)

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            "SELECT user_id, memory_type, content, importance FROM conversation_memory WHERE user_id = ? ORDER BY create_time DESC LIMIT 10",
            (user_id,)
        ).fetchall()
        print(f"conversation_memory 表: {len(rows)} 条")
        for r in rows:
            print(f"  [{r['memory_type']}] importance={r['importance']:.1f} {r['content'][:80]}")

        rows = conn.execute(
            "SELECT * FROM user_profile WHERE user_id = ?",
            (user_id,)
        ).fetchall()
        print(f"\nuser_profile 表: {len(rows)} 条")
        for r in rows:
            print(f"  专业领域: {r['expertise_domain'] or '未设置'}")
            print(f"  回答风格: {r['response_style'] or '未设置'}")
            facts = json.loads(r['key_facts'] or '[]')
            print(f"  key_facts: {facts}")

        conn.close()
    except Exception as e:
        print(f"数据库查询失败: {e}")

    print()
    print("=" * 60)
    print("第3步: 记忆注入验证（第二次对话）")
    print("=" * 60)

    query2 = "帮我写一个数据库查询优化的方案"

    print(f"用户: {query2}")
    resp = requests.post(f"{BASE_URL}/chat/kb_chat", json={
        "query": query2,
        "mode": "local_kb",
        "kb_name": kb_name,
        "stream": False,
    }, headers=headers)
    if resp.status_code == 200:
        r = resp.json()
        answer = parse_content(r)
        print(f"AI: {answer[:400]}...")

        # 检查回答是否有个性化特征
        checks = []
        if "代码示例" in answer or "```" in answer:
            checks.append("✓ 包含代码示例（用户偏好）")
        if "后端" in answer or "开发" in answer:
            checks.append("✓ 提及后端开发相关")
        if "张三" in answer:
            checks.append("✓ 记住了用户名")

        if checks:
            print(f"\n个性化验证:")
            for c in checks:
                print(f"  {c}")
        else:
            print(f"\n⚠ 回答未明显体现个性化，检查服务端日志中 'Memory extracted' 和 'Loaded memory' 关键字")
    else:
        print(f"请求失败: {resp.status_code}")
        print(f"响应: {resp.text[:300]}")

    print()
    print("=" * 60)
    print("同时请检查服务端控制台日志，搜索关键字:")
    print("  Memory extracted")
    print("  Loaded memory")
    print("=" * 60)


if __name__ == "__main__":
    main()
