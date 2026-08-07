"""
Mini Agent 权限控制模块 (Permission Management)
提供黑名单硬拦截、高风险操作规则检查以及终端用户授权询问机制。
"""

# 硬黑名单：高危指令直接拦截（无须向用户确认）
DENY_BASH_PATTERNS = [
    "rm -rf /",
    "shutdown",
    "reboot",
    "format ",
    "drop database",
    "git push -f",
    "git push --force",
    "git reset --hard"
]

# 规则配置：触发软确认的高风险/敏感操作模式 (跨平台兼容 Windows / Linux)
NEED_CONFIRM_PATTERNS = [
    "git push",
    "rm ",
    "del ",
    "erase ",
    "rd ",
    "rmdir",
    "remove-item",
    "pip install",
    "uv add",
    "uv remove",
    "uv pip",
    "npm install",
    "git checkout -f",
    "git clean"
]




def check_deny_list(command: str) -> str | None:
    """检查硬黑名单命令"""
    cmd_lower = command.lower()
    for pattern in DENY_BASH_PATTERNS:
        if pattern in cmd_lower:
            return f"包含极高风险指令 '{pattern}'，已触发系统安全拦截。"
    return None


def check_rules(name: str, args: dict) -> str | None:
    """检查规则引擎，判断是否需要提示用户授权确认"""
    # 1. 读文件、获取目录树等只读工具自动放行
    if name in ["read_file", "get_file_tree"]:
        return None

    # 2. 对 bash 命令检查敏感/高风险指令模式
    if name == "bash":
        command = args.get("command", "")
        cmd_lower = command.lower()
        for pattern in NEED_CONFIRM_PATTERNS:
            if pattern in cmd_lower:
                return f"命令包含高风险/敏感操作模式 '{pattern}'"

    return None


def ask_user(name: str, args: dict, reason: str) -> str:
    """在终端向用户请求授权确认"""
    print(f"\n\033[33m[警告] [权限提示] Agent 申请执行高风险工具: {name}\033[0m")

    print(f"   参数: {args}")
    print(f"   原因: {reason}")

    choice = input("\033[1;36m按 [y/Y] 批准执行，按其他任意键拒绝 >> \033[0m").strip().lower()
    return "allow" if choice in ["y", "yes"] else "deny"


def check_permission(name: str, args: dict) -> tuple[bool, str]:
    """
    核心权限检查入口函数
    :param name: 工具名称
    :param args: 工具参数字典
    :return: (is_allowed, deny_reason)
    """
    # Step 1: 检查 bash 命令的系统硬黑名单
    if name == "bash":
        command = args.get("command", "")
        deny_reason = check_deny_list(command)
        if deny_reason:
            return False, deny_reason

    # Step 2: 检查软规则，判断是否需要用户交互确认
    rule_reason = check_rules(name, args)
    if rule_reason:
        decision = ask_user(name, args, rule_reason)
        if decision == "deny":
            return False, "用户在权限确认提示中拒绝了授权。"

    # 默认放行
    return True, ""
