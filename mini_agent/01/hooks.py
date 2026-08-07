"""
Mini Agent 钩子系统 (Hooks System)
定义并主动注册 5 大核心内置钩子：
1. UserPromptSubmit -> user_prompt_hook (输入清洗)
2. PreToolUse        -> permission_hook (权限校验与黑名单拦截)
3. PreToolUse        -> log_hook (工具调用审计日志)
4. PostToolUse       -> large_output_hook (超长输出截断保护)
5. Stop              -> summary_hook (会话结束总结审计)
"""
from typing import Callable, Dict, List, Any
from tools import TOOL_HANDLERS
from permission import check_permission

# 全局钩子字典
HOOKS: Dict[str, List[Callable]] = {
    "UserPromptSubmit": [],
    "PreToolUse": [],
    "PostToolUse": [],
    "Stop": []
}


def register_hook(event: str, callback: Callable):
    """注册钩子回调函数"""
    if event not in HOOKS:
        raise ValueError(f"不支持的钩子事件: '{event}'，可选事件: {list(HOOKS.keys())}")
    HOOKS[event].append(callback)


def register_tool_to_hook(event: str, tool_name: str, tool_args: dict | None = None):
    """【往钩子注册工具】当钩子触发时自动调用绑定的工具"""
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
    """
    按顺序触发指定事件下的所有回调
    如果某个回调返回非 None 结果，表示触发拦截/覆盖，直接返回该结果终止后续钩子
    """
    if event not in HOOKS:
        return None

    for callback in HOOKS[event]:
        try:
            result = callback(*args)
            if result is not None:  # 教学用快捷方式：阻止此工具调用或覆盖返回值
                return result
        except Exception as e:
            print(f"\033[31m[Hook 运行异常] 事件 '{event}' 钩子处理失败: {e}\033[0m")

    return None


# ── 具体的 5 大内置 Hook 处理函数实现 ──

def user_prompt_hook(prompt: str):
    """1. UserPromptSubmit 钩子：输入清洗与预处理点"""
    cleaned = prompt.strip()
    return None

def permission_hook(name: str, args: dict):
    """2. PreToolUse 钩子 1：硬黑名单及高风险权限拦截"""
    allowed, deny_reason = check_permission(name, args)
    if not allowed:
        print(f"\033[31m[拦截] [权限钩子拦截] 工具 {name} 被拦截: {deny_reason}\033[0m")

        return f"权限拒绝：工具 {name} 执行被拦截或用户拒绝。原因: {deny_reason}。请调整方案或询问用户。"
    return None

def log_hook(name: str, args: dict):
    """3. PreToolUse 钩子 2：打印调起工具的审计日志"""
    print(f"\033[90m[Audit Hook] 即将调用工具: {name} | 参数: {args}\033[0m")
    return None

def large_output_hook(name: str, args: dict, output: str):
    """4. PostToolUse 钩子：超长输出截断保护，防止 token 溢出"""
    max_len = 5000
    if isinstance(output, str) and len(output) > max_len:
        print(f"\033[33m[Output Hook] 工具 {name} 输出过长({len(output)}字符)，自动截断至 {max_len} 字符\033[0m")
        truncated = output[:max_len] + f"\n... (系统 Hook 自动截断：输出超长，已省去后续 {len(output) - max_len} 字符)"
        return truncated
    return None

def summary_hook(messages: list, reason: str):
    """5. Stop 钩子：任务完成总结审计点"""
    print(f"\033[32m[Stop Hook] Agent 会话结束。结束原因: {reason} | 消息历史: {len(messages)} 条\033[0m")
    return None


# ── 默认注册所有 5 大内置钩子 ──
def init_default_hooks():
    """显式初始化默认内置钩子注册表"""
    for key in HOOKS:
        HOOKS[key].clear()

    register_hook("UserPromptSubmit", user_prompt_hook)
    register_hook("PreToolUse", permission_hook)
    register_hook("PreToolUse", log_hook)
    register_hook("PostToolUse", large_output_hook)
    register_hook("Stop", summary_hook)