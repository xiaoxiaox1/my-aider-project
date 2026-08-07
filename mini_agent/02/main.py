#!/usr/bin/env python3
import sys
from config import BASE_URL, MODEL, SYSTEM_PROMPT
from agent import agent_loop
from hooks import trigger_hooks, init_default_hooks
from file_index import GLOBAL_INDEXER
from git_undo import undo_last_checkpoint

def main():
    init_default_hooks()

    print("=" * 60)
    print("[Mini Agent 02 工业级重构版已就位]")
    print(f"🔗 服务地址: {BASE_URL}")
    print(f"🧠 驱动模型: {MODEL}")
    
    # 启动时自动全量扫描并生成内存索引
    GLOBAL_INDEXER.scan_workspace()
    
    print("💡 提示：输入任务需求；输入 /undo 一键撤销上一轮修改；输入 q 退出")
    print("=" * 60 + "\n")

    history = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            user_input = input("\033[1;32mUser >> \033[0m").strip()
            if not user_input:
                continue
            if user_input.lower() in ("q", "quit", "exit"):
                print("👋 感谢使用，再见！")
                break

            # 处理一键撤销 /undo 命令
            if user_input.lower() in ("/undo", "undo"):
                res = undo_last_checkpoint()
                print(res)
                # 重新扫描更新全仓库内存索引
                GLOBAL_INDEXER.scan_workspace()
                continue

            history.append({"role": "user", "content": user_input})
            agent_loop(history)
        except (KeyboardInterrupt, EOFError):
            print("\n👋 程序强制中断退出。")
            break

if __name__ == "__main__":
    main()
