#!/usr/bin/env python3
import sys
from config import BASE_URL, MODEL, SYSTEM_PROMPT
from agent import agent_loop

def main():
    print("=" * 60)
    print("🤖 欢迎使用 Mini Agent (模块化版本)")
    print(f"🔗 专属服务地址: {BASE_URL}")
    print(f"🧠 当前驱动模型: {MODEL}")
    print("💡 提示：输入任务需求（如：写一个 fib 函数并用 pytest 测试），输入 q 退出")
    print("=" * 60 + "\n")

    # 初始化对话历史，首条压入 SYSTEM_PROMPT
    history = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            user_input = input("\033[1;32mUser >> \033[0m").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n再见！")
            sys.exit(0)

        if not user_input:
            continue
        if user_input.lower() in ("q", "quit", "exit"):
            print("退出 Mini Agent。")
            break

        # 压入用户需求
        history.append({"role": "user", "content": user_input})
        
        # 调起 Agent 主循环处理
        agent_loop(history)
        print("\n" + "-" * 60)

if __name__ == "__main__":
    main()
