#!/usr/bin/env python3
"""
知识库内容处理流程
- 接收飞书消息
- 自动标签建议
- Markdown 写入 vault
"""
import os
import re
import json
import hashlib
from datetime import datetime
from pathlib import Path

VAULT_PATH = os.path.expanduser("~/Obsidian/Vault")
NOTES_PATH = os.path.join(VAULT_PATH, "_notes")
ASSETS_PATH = os.path.join(VAULT_PATH, "_assets")

# 确保目录存在
os.makedirs(NOTES_PATH, exist_ok=True)
os.makedirs(ASSETS_PATH, exist_ok=True)

# 标签关键词映射
TAG_KEYWORDS = {
    "#idea": ["idea", "想法", "灵感", "突发", "构思"],
    "#question": ["问题", "疑问", "怎么", "如何", "为什么", "?"],
    "#project": ["项目", "project", "任务", "开发"],
    "#learn": ["学习", "笔记", "教程", "学到了"],
    "#work": ["工作", "会议", "todo", "待办"],
    "#life": ["生活", "日常", "记录"],
    "#inbox": ["收集", "稍后"],
}

def suggest_tags(content: str) -> list:
    """根据内容自动建议标签"""
    content_lower = content.lower()
    tags = ["#inbox"]  # 默认添加收集箱标签
    
    for tag, keywords in TAG_KEYWORDS.items():
        for kw in keywords:
            if kw in content_lower:
                if tag not in tags:
                    tags.append(tag)
                break
    
    return tags

def generate_filename(title: str) -> str:
    """生成唯一文件名"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = re.sub(r'[^\w\u4e00-\u9fff]', '', title)[:20]
    return f"{timestamp}_{safe_title}.md"

def process_message(text: str, sender: str = "unknown") -> dict:
    """处理消息并写入 vault"""
    # 提取标题（第一行或前50字）
    lines = text.strip().split('\n')
    title = lines[0][:50] if lines else "untitled"
    
    # 建议标签
    tags = suggest_tags(text)
    tags_str = " ".join(tags)
    
    # 生成文件内容
    content = f"""---
title: {title}
date: {datetime.now().isoformat()}
tags: [{', '.join(tags)}]
author: {sender}
---

# {title}

{text}

---
*自动处理于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    # 写入文件
    filename = generate_filename(title)
    filepath = os.path.join(NOTES_PATH, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return {
        "status": "success",
        "filename": filename,
        "filepath": filepath,
        "tags_suggested": tags,
        "title": title
    }

def review_pending_notes():
    """回顾待处理笔记"""
    pending = []
    for f in os.listdir(NOTES_PATH):
        if f.endswith('.md'):
            filepath = os.path.join(NOTES_PATH, f)
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
                if '#inbox' in content:
                    pending.append({
                        "file": f,
                        "preview": content[:200]
                    })
    return pending

if __name__ == "__main__":
    # 测试
    test_msg = "我想到了一个很好的idea，关于AI助手的未来发展"
    result = process_message(test_msg, "test_user")
    print(json.dumps(result, ensure_ascii=False, indent=2))
