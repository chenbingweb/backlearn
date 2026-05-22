"""
Todo CLI - 命令行任务管理器

使用方法:
    python main.py add "买牛奶" --priority high
    python main.py list
    python main.py done 1
    python main.py delete 1

这就是你的第一个真实项目。遇到不会的，去查文档第 X 天。
"""

import json
import os
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional


# ========== 数据模型 ==========

@dataclass
class Task:
    """单个任务"""
    id: int
    content: str
    done: bool = False
    priority: str = "normal"  # low, normal, high
    created_at: str = ""
    done_at: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    def mark_done(self):
        """标记完成"""
        self.done = True
        self.done_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(**data)

    def __str__(self) -> str:
        status = "[x]" if self.done else "[ ]"
        priority_emoji = {"high": "🔥", "normal": "", "low": "🌱"}.get(self.priority, "")
        return f"{status} #{self.id} {priority_emoji} {self.content}"


# ========== 核心应用 ==========

class TodoApp:
    """任务管理应用"""

    def __init__(self, data_file: str = "tasks.json"):
        self.data_file = data_file
        self._tasks: List[Task] = []
        self._next_id = 1
        self._load()

    # ---- 增删改查 ----

    def add(self, content: str, priority: str = "normal") -> Task:
        """添加任务"""
        task = Task(
            id=self._next_id,
            content=content,
            priority=priority
        )
        self._tasks.append(task)
        self._next_id += 1
        self._save()
        return task

    def list(self, filter_status: Optional[str] = None) -> List[Task]:
        """列出任务

        filter_status: all, done, pending
        """
        tasks = self._tasks
        if filter_status == "done":
            tasks = [t for t in tasks if t.done]
        elif filter_status == "pending":
            tasks = [t for t in tasks if not t.done]
        return tasks

    def done(self, task_id: int) -> Optional[Task]:
        """标记完成"""
        task = self._find(task_id)
        if task:
            task.mark_done()
            self._save()
        return task

    def delete(self, task_id: int) -> bool:
        """删除任务"""
        task = self._find(task_id)
        if task:
            self._tasks.remove(task)
            self._save()
            return True
        return False

    def clear_done(self) -> int:
        """清除已完成的任务，返回删除数量"""
        before = len(self._tasks)
        self._tasks = [t for t in self._tasks if not t.done]
        after = len(self._tasks)
        self._save()
        return before - after

    # ---- 统计 ----

    def stats(self) -> dict:
        total = len(self._tasks)
        done = sum(1 for t in self._tasks if t.done)
        return {
            "total": total,
            "done": done,
            "pending": total - done,
            "completion_rate": f"{done/total*100:.1f}%" if total > 0 else "0%"
        }

    # ---- 内部方法 ----

    def _find(self, task_id: int) -> Optional[Task]:
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None

    def _save(self):
        """保存到 JSON 文件"""
        data = {
            "tasks": [t.to_dict() for t in self._tasks],
            "next_id": self._next_id
        }
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load(self):
        """从 JSON 文件加载"""
        if not os.path.exists(self.data_file):
            return
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
            self._next_id = data.get("next_id", 1)
        except (json.JSONDecodeError, KeyError):
            pass


# ========== 装饰器工具 ==========


def timer(func):
    """计时装饰器 - 对应文档第12天"""
    import functools
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"  ({time.time() - start:.4f}s)")
        return result
    return wrapper


def log_action(func):
    """日志装饰器 - 对应文档第12天"""
    import functools
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        action = func.__name__
        print(f"[LOG] {action}: args={args}, result={result is not None}")
        return result
    return wrapper
