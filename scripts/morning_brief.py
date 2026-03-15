#!/usr/bin/env python3
"""
早安日报 - 每日 9:30 自动发送
整合 Google Workspace、日历、天气（仅恶劣天气）、Apple Reminders
"""

import os
import sys
import json
import logging
import subprocess
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# 配置日志
LOG_DIR = os.path.expanduser("~/.openclaw/logs")
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(f"{LOG_DIR}/morning_brief.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("morning_brief")

# 配置
TIMEOUT = 10  # API 超时时间（秒）
MAX_RETRIES = 3  # 最大重试次数
RETRY_DELAYS = [1, 2, 4]  # 指数退避（秒）
WEATHER_BAD_CONDITIONS = ['暴雨', '台风', '极端高温', '极端低温', 'storm', 'typhoon', 'extreme']


def run_with_retry(cmd: list, timeout: int = TIMEOUT) -> tuple[bool, str]:
    """带重试机制的命令执行"""
    for attempt in range(MAX_RETRIES):
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            if result.returncode == 0:
                return True, result.stdout
            else:
                logger.warning(f"命令执行失败 (尝试 {attempt + 1}/{MAX_RETRIES}): {result.stderr}")
        except subprocess.TimeoutExpired:
            logger.warning(f"命令执行超时 (尝试 {attempt + 1}/{MAX_RETRIES})")
        except Exception as e:
            logger.warning(f"命令执行异常 (尝试 {attempt + 1}/{MAX_RETRIES}): {e}")
        
        if attempt < MAX_RETRIES - 1:
            sleep_time = RETRY_DELAYS[attempt]
            logger.info(f"等待 {sleep_time}s 后重试...")
            time.sleep(sleep_time)
    
    return False, ""


def get_calendar_events() -> Dict[str, Any]:
    """获取今日日历事件"""
    logger.info("获取 Google 日历事件...")
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # 使用 gog 获取日历事件
    cmd = ["gog", "calendar", "events", "primary", "--from", today, "--to", tomorrow, "--json"]
    success, output = run_with_retry(cmd)
    
    if success and output:
        try:
            events = json.loads(output)
            return {"status": "success", "data": events}
        except json.JSONDecodeError as e:
            logger.error(f"解析日历 JSON 失败: {e}")
            return {"status": "error", "message": "解析失败"}
    
    return {"status": "error", "message": "获取失败"}


def get_gmail_summary() -> Dict[str, Any]:
    """获取 Gmail 未读邮件摘要"""
    logger.info("获取 Gmail 未读邮件...")
    
    cmd = ["gog", "gmail", "search", "newer_than:1d", "--max", "5", "--json"]
    success, output = run_with_retry(cmd)
    
    if success and output:
        try:
            messages = json.loads(output)
            return {"status": "success", "count": len(messages), "data": messages}
        except json.JSONDecodeError:
            return {"status": "error", "message": "解析失败"}
    
    return {"status": "error", "message": "获取失败"}


def get_weather() -> Optional[Dict[str, Any]]:
    """获取天气（仅恶劣天气时返回）"""
    logger.info("获取天气信息...")
    
    # 获取详细天气数据
    cmd = ["curl", "-s", "wttr.in/Shanghai?format=j1"]
    success, output = run_with_retry(cmd, timeout=15)
    
    if not success or not output:
        return None
    
    try:
        data = json.loads(output)
        current = data.get("current_condition", [{}])[0]
        temp = int(current.get("temp_C", 0))
        condition = current.get("weatherDesc", [{}])[0].get("value", "")
        weather_code = current.get("weatherCode", "0")
        
        # 检查是否为恶劣天气
        # 天气码: 308(暴雨), 200-232(雷暴), 900+(极端)
        bad_weather_codes = ["308", "309", "310", "311", "312", "313", "314", "315", "316", "317", "318", "200", "201", "202", "210", "211", "212", "221", "230", "231", "232", "900", "901", "902", "903", "904", "905", "906", "957", "958", "959", "960", "961", "962"]
        
        is_bad = weather_code in bad_weather_codes or any(bad in condition.lower() for bad in WEATHER_BAD_CONDITIONS)
        
        # 检查极端温度
        if temp >= 38 or temp <= 0:
            is_bad = True
        
        if is_bad:
            logger.info(f"检测到恶劣天气: {condition}, 温度: {temp}°C")
            return {
                "status": "bad_weather",
                "condition": condition,
                "temp": temp,
                "message": f"⚠️ 恶劣天气提醒: {condition}, {temp}°C"
            }
        else:
            logger.info(f"天气正常: {condition}, {temp}°C, 不发送")
            return None
            
    except (json.JSONDecodeError, IndexError, KeyError) as e:
        logger.error(f"解析天气数据失败: {e}")
        return None


def get_reminders() -> Dict[str, Any]:
    """获取今日提醒事项"""
    logger.info("获取今日提醒...")
    
    cmd = ["remindctl", "today", "--json"]
    success, output = run_with_retry(cmd)
    
    if success and output:
        try:
            reminders = json.loads(output)
            return {"status": "success", "count": len(reminders), "data": reminders}
        except json.JSONDecodeError:
            return {"status": "error", "message": "解析失败"}
    
    return {"status": "error", "message": "获取失败"}


def format_message(calendar_data: Dict, gmail_data: Dict, weather_data: Optional[Dict], reminders_data: Dict) -> str:
    """格式化飞书消息"""
    lines = ["☀️ **早安日报**", f"📅 {datetime.now().strftime('%Y年%m月%d日 %A')}", ""]
    
    # 天气（仅恶劣天气）
    if weather_data:
        lines.append(f"{weather_data['message']}")
        lines.append("")
    
    # 日历
    if calendar_data.get("status") == "success":
        events = calendar_data.get("data", [])
        if events:
            lines.append("📅 **今日日程**")
            for event in events[:5]:  # 最多显示5个
                start = event.get("start", {}).get("dateTime", "")[11:16] if event.get("start", {}).get("dateTime") else "全天"
                summary = event.get("summary", "无标题")
                lines.append(f"  • {start} {summary}")
            lines.append("")
        else:
            lines.append("📅 **今日日程**: 无安排")
            lines.append("")
    else:
        lines.append("📅 **今日日程**: ⚠️ 部分数据获取失败")
        lines.append("")
    
    # 邮件
    if gmail_data.get("status") == "success":
        count = gmail_data.get("count", 0)
        lines.append(f"📧 **今日邮件**: {count} 封新邮件")
        lines.append("")
    else:
        lines.append("📧 **今日邮件**: ⚠️ 部分数据获取失败")
        lines.append("")
    
    # 提醒
    if reminders_data.get("status") == "success":
        reminders = reminders_data.get("data", [])
        if reminders:
            lines.append("⏰ **今日提醒**")
            for r in reminders[:5]:  # 最多显示5个
                title = r.get("title", "无标题")
                due = r.get("dueDate", "")
                lines.append(f"  • {title}" + (f" (due: {due})" if due else ""))
            lines.append("")
        else:
            lines.append("⏰ **今日提醒**: 无")
            lines.append("")
    else:
        lines.append("⏰ **今日提醒**: ⚠️ 部分数据获取失败")
        lines.append("")
    
    return "\n".join(lines)


def send_feishu_message(message: str) -> bool:
    """发送飞书消息"""
    logger.info("发送飞书消息...")
    
    # 读取太子所在的群聊 ID
    chat_id = os.environ.get("FEISHU_TAIZI_CHAT_ID")
    if not chat_id:
        # 尝试从配置文件读取
        config_path = os.path.expanduser("~/.openclaw/workspace-taizi/config/morning_brief.json")
        if os.path.exists(config_path):
            try:
                with open(config_path) as f:
                    config = json.load(f)
                    chat_id = config.get("chat_id")
            except:
                pass
    
    if not chat_id:
        logger.error("未配置飞书群聊 ID")
        return False
    
    # 使用 openclaw message 命令发送
    cmd = ["openclaw", "message", "send", "--channel", "feishu", "--chat-id", chat_id, "--message", message]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            logger.info("飞书消息发送成功")
            return True
        else:
            logger.error(f"飞书消息发送失败: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"发送飞书消息异常: {e}")
        return False


def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("开始执行早安日报...")
    
    results = {
        "calendar": {"status": "skipped"},
        "gmail": {"status": "skipped"},
        "weather": None,
        "reminders": {"status": "skipped"}
    }
    
    # 1. 获取日历
    results["calendar"] = get_calendar_events()
    
    # 2. 获取邮件
    results["gmail"] = get_gmail_summary()
    
    # 3. 获取天气（仅判断是否恶劣）
    results["weather"] = get_weather()
    
    # 4. 获取提醒
    results["reminders"] = get_reminders()
    
    # 5. 格式化消息
    message = format_message(
        results["calendar"],
        results["gmail"],
        results["weather"],
        results["reminders"]
    )
    
    # 6. 发送飞书消息
    success = send_feishu_message(message)
    
    # 7. 保存结果
    output_file = f"{LOG_DIR}/morning_brief_{datetime.now().strftime('%Y%m%d')}.json"
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "message_sent": success
        }, f, ensure_ascii=False, indent=2)
    
    logger.info(f"早安日报执行完成，消息发送: {'成功' if success else '失败'}")
    logger.info("=" * 50)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
