import json
from llm import call_local_llm
from tools import TOOL_HANDLERS
from hooks import trigger_hooks



def agent_loop(messages: list):
    """核心 Agent 主循环：驱动大模型思考 ➔ 钩子拦截 ➔ 权限校验 ➔ 工具执行 ➔ 报错自愈 ➔ Stop 钩子"""
    while True:
        # 1. 发送 HTTP 请求调用大模型
        response_msg, finish_reason = call_local_llm(messages)
        
        # 2. 校验响应：如果请求出错，触发 Stop 钩子并退出循环
        if finish_reason == "error" or not response_msg:
            print("\033[31m[提示]\033[0m LLM 服务未正常响应，已终止当前轮次。")
            trigger_hooks("Stop", messages, "error")
            break

        # 3. 将完整的 assistant 响应存入上下文 (必须包含 tool_calls，满足 400 校验)
        messages.append(response_msg)
        
        # 4. 打印大模型的自然语言回复
        content = response_msg.get("content")
        if content:
            print(f"\033[34mAI >> {content}\033[0m")

        # 5. 如果 finish_reason 不是 "tool_calls"，说明回复完毕，触发 Stop 钩子并结束任务
        if finish_reason != "tool_calls":
            trigger_hooks("Stop", messages, finish_reason)
            break

        # 6. 遍历大模型返回的工具调用列表并执行
        tool_calls = response_msg.get("tool_calls") or []
        for call in tool_calls:
            info = call["function"]
            name = info["name"]
            raw_args = info["arguments"]
            call_id = call.get("id")

            # 将 JSON 参数解包为 Python 字典
            args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args

            print(f"\033[33m> 调起工具: {name}\033[0m")

            # ------------------ 🪝 1. PreToolUse 钩子点 (自动触发 permission_hook 与 log_hook) ------------------
            hook_override = trigger_hooks("PreToolUse", name, args)
            if hook_override is not None:
                output = hook_override
            else:
                # 钩子全员放行，正常执行工具
                handler = TOOL_HANDLERS.get(name)
                output = handler(**args) if handler else f"未知工具: {name}"

            
            # ------------------ 🪝 3. PostToolUse 钩子点 ------------------
            post_override = trigger_hooks("PostToolUse", name, args, output)
            if post_override is not None:
                output = post_override

            # 打印工具输出预览
            print(str(output)[:200])

            # 7. 按照 OpenAI 规范，以 role: tool 追加工具结果并附带 tool_call_id
            messages.append({
                "role": "tool",
                "tool_call_id": call_id,
                "content": str(output)
            })


