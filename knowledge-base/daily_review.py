#!/usr/bin/env python3
"""
每日知识库回顾提醒脚本
"""
import os
import json
from datetime import datetime

VAULT_PATH = os.path.expanduser("~/Obsidian/Vault/_notes")

def get_review_summary():
    """获取待回顾内容"""
    pending = []
    total = 0
    
    if os.path.exists(VAULT_PATH):
        for f in os.listdir(VAULT_PATH):
            if f.endswith('.md'):
                total += 1
                filepath = os.path.join(VAULT_PATH, f)
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                    if '#inbox' in content or '#review' in content:
                        # 提取标题
                        for line in content.split('\n'):
                            if line.startswith('title:'):
                                title = line.replace('title:', '').strip()
                                pending.append(title)
                                break
    
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total_notes": total,
        "pending_review": len(pending),
        "items": pending[:5]  # 最多显示5条
    }

if __name__ == "__main__":
    result = get_review_summary()
    print(json.dumps(result, ensure_ascii=False, indent=2))
