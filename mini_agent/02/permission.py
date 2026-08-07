"""
Mini Agent 02 权限控制模块
"""

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
    cmd_lower = command.lower()
    for pattern in DENY_BASH_PATTERNS:
        if pattern in cmd_lower:
            return f"包含极高风险指令 '{pattern}'，已触发系统安全拦截。"
    return None


def check_rules(name: str, args: dict) -> str | None:
    if name in ["read_file", "get_file_tree"]:
        return None

    if name == "bash":
        command = args.get("command", "")
        cmd_lower = command.lower()
        for pattern in NEED_CONFIRM_PATTERNS:
            if pattern in cmd_lower:
                return f"命令包含高风险/敏感操作模式 '{pattern}'"

    return None


def ask_user(name: str, args: dict, reason: str) -> str:
    print(f"\n\033[33m[警告] [权限提示] Agent 申请执行高风险工具: {name}\033[0m")
    print(f"   参数: {args}")
    print(f"   原因: {reason}")
    choice = input("\033[1;36m按 [y/Y] 批准执行，按其他任意键拒绝 >> \033[0m").strip().lower()
    return "allow" if choice in ["y", "yes"] else "deny"


def check_permission(name: str, args: dict) -> tuple[bool, str]:
    if name == "bash":
        command = args.get("command", "")
        deny_reason = check_deny_list(command)
        if deny_reason:
            return False, deny_reason

    rule_reason = check_rules(name, args)
    if rule_reason:
        decision = ask_user(name, args, rule_reason)
        if decision == "deny":
            return False, "用户在权限确认提示中拒绝了授权。"

    return True, ""
