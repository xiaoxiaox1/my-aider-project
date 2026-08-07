import json
from llm import call_local_llm
from tools import TOOL_HANDLERS
from hooks import trigger_hooks
from error_injector import format_tool_error_guidance, is_tool_error


def estimate_tokens_in_messages(messages: list) -> int:
    """粗略估算 messages 消息历史的总 Token 数量 (按 1 Token ≈ 3.5 字符估算)"""
    total_chars = 0
    for msg in messages:
        content = msg.get("content") or ""
        if isinstance(content, str):
            total_chars += len(content)
        elif isinstance(content, list):
            total_chars += sum(len(str(c)) for c in content)
        tool_calls = msg.get("tool_calls")
        if tool_calls:
            total_chars += len(json.dumps(tool_calls, ensure_ascii=False))
    return int(total_chars / 3.5)


def print_token_stats(messages: list):
    """在对话轮次结束 (stop) 时打印醒目的提示词 Token 消耗看板 (GBK 控制台兼容版)"""
    tokens = estimate_tokens_in_messages(messages)
    msg_count = len(messages)
    print(f"\n\033[1;33m[Token 统计看板] 当前累计上下文总长: 约 {tokens} Tokens (共 {msg_count} 条消息)\033[0m")
    if tokens > 4000:
        print(f"\033[33m   [性能提示] 当前上下文已卡顿累积到 {tokens} Tokens。长上下文会显著增加远端 GPU 首 Token 预充填耗时，导致回复响应变慢！\033[0m")



def agent_loop(messages: list):
    """核心 Agent 主循环 (支持 02 工业级 Diff Engine、错误引导注入与 3 次失败连续熔断机制)"""
    consecutive_failures = 0
    failed_tools_chain = []

    while True:
        response_msg, finish_reason = call_local_llm(messages)
        
        if finish_reason == "error" or not response_msg:
            print("\033[31m[提示]\033[0m LLM 服务未正常响应，已终止当前轮次。")
            trigger_hooks("Stop", messages, "error")
            print_token_stats(messages)
            break

        messages.append(response_msg)
        
        content = response_msg.get("content")
        if content:
            print(f"\033[34mAI >> {content}\033[0m")

        if finish_reason != "tool_calls":
            trigger_hooks("Stop", messages, finish_reason)
            print_token_stats(messages)
            break


        tool_calls = response_msg.get("tool_calls") or []
        for call in tool_calls:
            info = call["function"]
            name = info["name"]
            raw_args = info["arguments"]
            call_id = call.get("id")

            args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args

            print(f"\033[33m> 调起工具: {name}\033[0m")

            hook_override = trigger_hooks("PreToolUse", name, args)
            if hook_override is not None:
                output = hook_override
            else:
                handler = TOOL_HANDLERS.get(name)
                output = handler(**args) if handler else f"未知工具: {name}"

            post_override = trigger_hooks("PostToolUse", name, args, output)
            if post_override is not None:
                output = post_override

            # 检测失败状态与熔断计数
            if is_tool_error(str(output)):
                consecutive_failures += 1
                failed_tools_chain.append(name)
            else:
                consecutive_failures = 0
                failed_tools_chain.clear()

            # 工具失败提示词差异化自动注入
            final_output = format_tool_error_guidance(name, args, str(output))

            print(str(output)[:200])

            messages.append({
                "role": "tool",
                "tool_call_id": call_id,
                "content": final_output
            })

            # -------------------------------------------------------------
            # 强行熔断防线: 工具连续执行失败达到 3 次，立刻打断循环
            # -------------------------------------------------------------
            if consecutive_failures >= 3:
                circuit_breaker_msg = (
                    f"[CIRCUIT_BREAKER_ALERT: 系统安全熔断告警!]\n"
                    f"检测到工具连续 3 次执行失败 (失败链路: {' -> '.join(failed_tools_chain)})。\n"
                    f"为了防止大模型陷入无休止的死循环，系统已触发强行熔断机制打断！\n\n"
                    f"[强制行动指令]:\n"
                    f"1. 绝对禁止再次尝试发起任何工具调用！\n"
                    f"2. 请立即停止当前思考逻辑，向用户总结汇报这 3 次工具调用的失败原因与报错详情。\n"
                    f"3. 给出后续排查建议并等待用户新的指示。"
                )
                print(f"\n\033[1;31m[熔断告警] 工具连续 {consecutive_failures} 次执行失败 ({' -> '.join(failed_tools_chain)})，系统已触发安全熔断打断！\033[0m\n")
                
                messages.append({
                    "role": "system",
                    "content": circuit_breaker_msg
                })
                
                trigger_hooks("Stop", messages, "circuit_breaker_fused")
                print_token_stats(messages)
                return



