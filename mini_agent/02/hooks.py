"""
Mini Agent 02 钩子系统 (Hooks System)
"""
from typing import Callable, Dict, List
from tools import TOOL_HANDLERS
from permission import check_permission

HOOKS: Dict[str, List[Callable]] = {
    "UserPromptSubmit": [],
    "PreToolUse": [],
    "PostToolUse": [],
    "Stop": []
}


def register_hook(event: str, callback: Callable):
    if event not in HOOKS:
        raise ValueError(f"不支持的钩子事件: '{event}'")
    HOOKS[event].append(callback)


def register_tool_to_hook(event: str, tool_name: str, tool_args: dict | None = None):
    if tool_name not in TOOL_HANDLERS:
        raise ValueError(f"无法往钩子注册未知工具 '{tool_name}'")

    def tool_callback(*args):
        t_args = tool_args or {}
        print(f"\033[35m[Hook 自动调起工具] 事件: {event} -> 运行工具: {tool_name}({t_args})\033[0m")
        handler = TOOL_HANDLERS[tool_name]
        try:
            res = handler(**t_args)
            print(f"\033[35m[Hook 工具输出预览]\033[0m {str(res)[:150]}")
            return None
        except Exception as e:
            print(f"\033[31m[Hook 工具运行失败] {e}\033[0m")
            return None

    register_hook(event, tool_callback)


def trigger_hooks(event: str, *args):
    if event not in HOOKS:
        return None

    for callback in HOOKS[event]:
        try:
            result = callback(*args)
            if result is not None:
                return result
        except Exception as e:
            print(f"\033[31m[Hook 运行异常] 事件 '{event}' 钩子处理失败: {e}\033[0m")

    return None


def user_prompt_hook(prompt: str):
    return None

def permission_hook(name: str, args: dict):
    allowed, deny_reason = check_permission(name, args)
    if not allowed:
        print(f"\033[31m[拦截] [权限钩子拦截] 工具 {name} 被拦截: {deny_reason}\033[0m")
        return f"权限拒绝：工具 {name} 执行被拦截或用户拒绝。原因: {deny_reason}。"
    return None

def log_hook(name: str, args: dict):
    print(f"\033[90m[Audit Hook] 即将调用工具: {name} | 参数: {args}\033[0m")
    return None

def large_output_hook(name: str, args: dict, output: str):
    max_len = 5000
    if isinstance(output, str) and len(output) > max_len:
        print(f"\033[33m[Output Hook] 工具 {name} 输出过长({len(output)}字符)，自动截断至 {max_len} 字符\033[0m")
        return output[:max_len] + f"\n... (系统 Hook 自动截断：输出超长，已省去后续 {len(output) - max_len} 字符)"
    return None

def summary_hook(messages: list, reason: str):
    print(f"\033[32m[Stop Hook] Agent 会话结束。结束原因: {reason} | 消息历史: {len(messages)} 条\033[0m")
    return None


def init_default_hooks():
    for key in HOOKS:
        HOOKS[key].clear()

    register_hook("UserPromptSubmit", user_prompt_hook)
    register_hook("PreToolUse", permission_hook)
    register_hook("PreToolUse", log_hook)
    register_hook("PostToolUse", large_output_hook)
    register_hook("Stop", summary_hook)
