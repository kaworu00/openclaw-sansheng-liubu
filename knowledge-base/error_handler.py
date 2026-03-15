#!/usr/bin/env python3
"""
错误处理与告警模块
- 重试机制
- 告警通知
"""
import time
import json
import traceback
from functools import wraps
from datetime import datetime

# 告警级别
ALERT_LEVEL = {
    "INFO": 0,
    "WARNING": 1,
    "ERROR": 2,
    "CRITICAL": 3
}

class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self.alerts = []
        self.feishu_webhook = None  # 可配置飞书 webhook
    
    def add_alert(self, level: str, message: str, context: dict = None):
        """记录告警"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "context": context or {}
        }
        self.alerts.append(alert)
        
        # CRITICAL 级别自动发送通知
        if ALERT_LEVEL.get(level, 0) >= ALERT_LEVEL["CRITICAL"]:
            self._send_critical_alert(alert)
    
    def _send_critical_alert(self, alert: dict):
        """发送严重告警到飞书"""
        # TODO: 实现飞书消息发送
        print(f"🚨 CRITICAL ALERT: {alert}")
    
    def get_alerts(self, level: str = None):
        """获取告警记录"""
        if level:
            return [a for a in self.alerts if a["level"] == level]
        return self.alerts
    
    def clear(self):
        """清空告警记录"""
        self.alerts = []

# 全局告警管理器
alert_manager = AlertManager()

def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟（秒）
        backoff: 退避倍数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay
            
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts:
                        # 最后一次失败，记录 CRITICAL 告警
                        alert_manager.add_alert(
                            "CRITICAL",
                            f"Function {func.__name__} failed after {max_attempts} attempts",
                            {
                                "function": func.__name__,
                                "error": str(e),
                                "traceback": traceback.format_exc(),
                                "attempts": max_attempts
                            }
                        )
                        raise
                    
                    # 记录 WARNING 并重试
                    alert_manager.add_alert(
                        "WARNING",
                        f"Function {func.__name__} failed (attempt {attempt}/{max_attempts}), retrying...",
                        {"error": str(e), "attempt": attempt}
                    )
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
                    attempt += 1
            
            return None
        
        return wrapper
    return decorator

def safe_execute(fallback=None, alert_on_error: bool = True):
    """
    安全执行装饰器
    
    Args:
        fallback: 失败时的返回值
        alert_on_error: 是否记录告警
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if alert_on_error:
                    alert_manager.add_alert(
                        "ERROR",
                        f"Function {func.__name__} encountered an error",
                        {"error": str(e), "traceback": traceback.format_exc()}
                    )
                return fallback
        return wrapper
    return decorator

# 测试
if __name__ == "__main__":
    @retry(max_attempts=3, delay=0.5)
    def test_func():
        print("Executing test_func...")
        raise ValueError("Test error")
    
    try:
        test_func()
    except Exception as e:
        print(f"Final exception: {e}")
    
    print("\nAlerts recorded:")
    print(json.dumps(alert_manager.get_alerts(), ensure_ascii=False, indent=2))
