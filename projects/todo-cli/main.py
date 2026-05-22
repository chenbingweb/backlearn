#!/usr/bin/env python3
"""
Todo CLI - 命令行入口

跑起来:
    python main.py add "买牛奶"
    python main.py add "写代码" --priority high
    python main.py list
    python main.py list --filter pending
    python main.py done 1
    python main.py delete 2
    python main.py stats
    python main.py clear

这就是你的项目。没有教程，直接写代码、跑代码、改代码。
"""

import sys
from todo import TodoApp


def print_help():
    print("""
用法:
    python main.py add <内容> [--priority low|normal|high]
    python main.py list [--filter all|done|pending]
    python main.py done <id>
    python main.py delete <id>
    python main.py stats
    python main.py clear

示例:
    python main.py add "学习 FastAPI" --priority high
    python main.py list
    python main.py done 1
    python main.py stats
""")


def main():
    app = TodoApp()

    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1]

    # ---- add ----
    if command == "add":
        if len(sys.argv) < 3:
            print("错误: 需要输入任务内容")
            return

        content = sys.argv[2]
        priority = "normal"

        if "--priority" in sys.argv:
            idx = sys.argv.index("--priority")
            if idx + 1 < len(sys.argv):
                priority = sys.argv[idx + 1]

        task = app.add(content, priority)
        print(f"添加成功: {task}")

    # ---- list ----
    elif command == "list":
        filter_status = "all"
        if "--filter" in sys.argv:
            idx = sys.argv.index("--filter")
            if idx + 1 < len(sys.argv):
                filter_status = sys.argv[idx + 1]

        tasks = app.list(filter_status)
        if not tasks:
            print("没有任务")
            return

        print(f"\n任务列表 ({filter_status}):")
        print("-" * 40)
        for task in tasks:
            print(f"  {task}")
        print()

    # ---- done ----
    elif command == "done":
        if len(sys.argv) < 3:
            print("错误: 需要输入任务ID")
            return
        try:
            task_id = int(sys.argv[2])
        except ValueError:
            print("错误: ID 必须是数字")
            return

        task = app.done(task_id)
        if task:
            print(f"已完成: {task}")
        else:
            print(f"错误: 找不到任务 #{task_id}")

    # ---- delete ----
    elif command == "delete":
        if len(sys.argv) < 3:
            print("错误: 需要输入任务ID")
            return
        try:
            task_id = int(sys.argv[2])
        except ValueError:
            print("错误: ID 必须是数字")
            return

        if app.delete(task_id):
            print(f"已删除任务 #{task_id}")
        else:
            print(f"错误: 找不到任务 #{task_id}")

    # ---- stats ----
    elif command == "stats":
        stats = app.stats()
        print("\n统计:")
        print(f"  总计: {stats['total']}")
        print(f"  已完成: {stats['done']}")
        print(f"  待办: {stats['pending']}")
        print(f"  完成率: {stats['completion_rate']}")

    # ---- clear ----
    elif command == "clear":
        count = app.clear_done()
        print(f"已清除 {count} 个已完成任务")

    # ---- help ----
    else:
        print_help()


if __name__ == "__main__":
    main()
