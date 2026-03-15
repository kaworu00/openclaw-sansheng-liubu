# 🐲🦞 OpenClaw 扫盲版 - 给不会使用的同学看

> 来源：飞书 Wiki

## 定位
目前定位就是**个人助理**，给你一种做皇帝的感觉，情绪价值更足的东西。

## 能做什么？
多维度的 AI 人。看网页操作等等

## 官方部署文档
官方部署文档：一步一步来能解决好多问题。如果有问题看常见问题。

## 常见基础问题

### 1. 400 Total tokens of image and text exceed max message tokens
这个是上下文太大了。输入 `/new` 能解决，或者是 token 限额了。

### 2. 飞书如何配置多个龙虾？
没必要配置多个，OpenClaw 现在不稳定，多想想怎么搞稳定和优化 skill 来得更实际。
先玩一个，会了再玩多个。

### 3. 为什么开通了读取权限机器人没有消息输入框
检查下面几个点：
1. 有没有添加机器人权限
2. 回调里面事件有没有开启
3. 回调里面的长链接有没有点击配置保存？

### 4. api 限速 API rate limit reached. Please try again later.
需要等待或联系管理员提高限额

### 5. 如何保证本地部署的虾不休眠
需要保持电脑唤醒状态，或使用云服务器

### 6. 如何使用 OpenClaw 操作 Codex、Claude Code 等编程工具
需要安装对应工具并配置

## 好用的 Skill（持续补充中）

1. 小红书自动发布 skill 防止 ban 版本
2. 使用 OpenClaw 一句话发微信公众号文章
3. 帮你节省 tokens 的 skill（plan Lite 有福了）
4. 给你的龙虾装上眼睛的 skill（必备）
5. 一个电脑只能使用一个微信？NO，多开 skill 来了
6. 抖音视频解析技能
7. 组合拳解析抖音生成微信公众号文章
8. 🦞安全守门员 skill-vetter（特别是本机安装的一定要装）
9. 漫剧生成多风格版（使用字节的 seedance）
10. 一句话生成大师级设计海报
11. 小红薯封面图 Skills
12. 配置文件一定要定时备份 skill
13. playwright-skill（浏览器自动化技能）
14. tavily-search（AI 专用搜索引擎）
15. self-improving-agent（自我进化技能）
16. summarize（内容总结神器）

## 玩虾心法
遇到问题可以直接问 OpenClaw，它不回答就"口喷"它，大模型也有惰性。

遇到代码报错就把报错复制给千问或者 Gemini 问答，它们比我们聪明，能解决很多问题。

## 官方资源
- 官方插件开源：https://github.com/larksuite/openclaw-lark/blob/main/README.zh.md

---
*整理时间：2026年3月13日*
