"""记录每个Agent的输入/输出/耗时，供前端回放"""
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any


class TraceLogger:
    def __init__(self):
        self.events: list[dict] = []
        self._start_times: dict[str, float] = {}

    def start(self, agent_name: str, state_snapshot: dict):
        """Agent开始执行"""
        self._start_times[agent_name] = time.time()
        self.events.append({
            "type": "agent_start",
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "state_before": self._clean_for_json(state_snapshot),
        })

    def end(self, agent_name: str, state_after: dict, output: Any = None):
        """Agent结束执行"""
        duration_ms = int((time.time() - self._start_times.pop(agent_name, time.time())) * 1000)
        self.events.append({
            "type": "agent_end",
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "duration_ms": duration_ms,
            "output": self._clean_for_json(output) if output else None,
            "state_after_keys": list(state_after.keys()) if isinstance(state_after, dict) else None,
        })

    def log_event(self, event_type: str, **kwargs):
        """通用事件"""
        self.events.append({
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            **kwargs,
        })

    def dump(self, path: str):
        """导出 trace.json"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "trace_version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "events": self.events
            }, f, ensure_ascii=False, indent=2)

    def _clean_for_json(self, obj: Any) -> Any:
        """递归清理不可序列化的对象"""
        if isinstance(obj, dict):
            return {k: self._clean_for_json(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._clean_for_json(v) for v in obj]
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        return str(obj)


_logger: TraceLogger | None = None


def get_logger() -> TraceLogger:
    global _logger
    if _logger is None:
        _logger = TraceLogger()
    return _logger


def reset_logger() -> TraceLogger:
    """单测时重置，避免不同测试共用一个全局实例"""
    global _logger
    _logger = TraceLogger()
    return _logger
