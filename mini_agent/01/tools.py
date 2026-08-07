import os
import subprocess
from pathlib import Path
from config import WORKDIR

def safe_path(p: str) -> Path:
    """确保操作的文件路径在 WORKDIR 工作目录之内，防止路径遍历攻击"""
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"安全拒绝：路径企图越界访问 workspace 外部: {p}")
    return path

# ── 1. 工具 Handler 实现 ──

def run_read(path: str, limit: int | None = None) -> str:
    """读取本地文件内容"""
    try:
        target = safe_path(path)
        if not target.exists():
            return f"错误: 文件 {path} 不存在"
        lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
        if limit and limit < len(lines):
            lines = lines[:limit] + [f"... (省略后续 {len(lines) - limit} 行)"]
        return "\n".join(lines) if lines else "(文件内容为空)"
    except Exception as e:
        return f"读取文件错误: {e}"

def run_write(path: str, content: str) -> str:
    """全量创建或覆盖本地文件"""
    try:
        target = safe_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"成功写入文件: {path} ({len(content)} 字符)"
    except Exception as e:
        return f"写入文件错误: {e}"

def run_edit(path: str, old_str: str, new_str: str) -> str:
    """局部精确编辑文件 (Search & Replace)"""
    try:
        target = safe_path(path)
        if not target.exists():
            return f"错误：文件 {path} 不存在"
        content = target.read_text(encoding="utf-8")
        if old_str not in content:
            return f"编辑失败：在文件 {path} 中未匹配到指定的旧文本，请检查空格或缩进。"
        updated_content = content.replace(old_str, new_str, 1)
        target.write_text(updated_content, encoding="utf-8")
        return f"成功编辑文件: {path}"
    except Exception as e:
        return f"编辑文件失败: {e}"

def run_bash(command: str) -> str:
    """在工作目录下运行终端命令"""
    dangerous = ["rm -rf /", "shutdown", "reboot", "format "]
    if any(d in command for d in dangerous):
        return "错误：检测到危险命令，已拦截"
    try:
        r = subprocess.run(
            command,
            shell=True,
            cwd=WORKDIR,
            capture_output=True,
            text=True,
            timeout=120,
            encoding="utf-8",
            errors="replace"
        )
        out = (r.stdout + r.stderr).strip()
        return out[:10000] if out else "(命令执行成功，无输出)"
    except subprocess.TimeoutExpired:
        return "错误：命令执行超时 (120秒)"
    except Exception as e:
        return f"命令执行失败: {e}"
def run_get_file_tree(path:str='.'):
    try:
        target = safe_path(path)
        if not target.exists():
            return f"错误: 目录 {path} 不存在"
        ignore_dir =  {".git", "__pycache__", ".venv", ".idea"}
        tree = []
        for root, dirs, files in os.walk(target):
            dirs[:] = [d for d in dirs if d not in ignore_dir]
            rel_path = os.path.relpath(root, WORKDIR)
            level = 0 if rel_path == "." else rel_path.count(os.sep) + 1
            indent = "  " * level
            folder_name = os.path.basename(root) if rel_path != "." else "."

            tree.append(f"{indent}📁 {folder_name}/")
            for f in files:
                tree.append(f"{indent}  📄 {f}")

        return "\n".join(tree) if tree else "(工作区为空目录)"
    except Exception as e:
        return f"获取目录树失败: {e}"

DENY_LIST = ["rm -rf /", "sudo", "shutdown", "reboot", "mkfs", "dd if=", "> /dev/sda"]

def check_deny_list(command: str) -> str | None:
    for pattern in DENY_LIST:
        if pattern in command:
            return f"Blocked: '{pattern}' is on the deny list"
    return None

PERMISSION_RULES = [
    {"tools": ["read_file", "write_file", "edit_file"],
     "check": lambda args: not (WORKDIR / args.get("path", "")).resolve().is_relative_to(WORKDIR),
     "message": "Writing outside workspace"},
    {"tools": ["bash"],
     "check": lambda args: any(kw in args.get("command", "") for kw in ["rm ", "> /etc/", "chmod 777"]),
     "message": "Potentially destructive command"},
]

def check_rules(tool_name: str, args: dict) -> str | None:
    for rule in PERMISSION_RULES:
        if tool_name in rule["tools"] and rule["check"](args):
            return rule["message"]
    return None

# Gate 3: User approval — wait for confirmation after rule match
def ask_user(tool_name: str, args: dict, reason: str) -> str:
    print(f"\n\033[33m⚠  {reason}\033[0m")
    print(f"   Tool: {tool_name}({args})")
    choice = input("   Allow? [y/N] ").strip().lower()
    return "allow" if choice in ("y", "yes") else "deny"


def check_permission(block) -> bool:
    if block.name == "bash":
        reason = check_deny_list(block.input.get("command", ""))
        if reason:
            print(f"\n\033[31m⛔ {reason}\033[0m")
            return False
    reason = check_rules(block.name, block.input)
    if reason:
        decision = ask_user(block.name, block.input, reason)
        if decision == "deny":
            return False
    return True



# 核心内存 Todo 状态
CURRENT_TODOS: list[dict] = []

def run_todo_write(todos: list[dict]) -> str:
    """创建或更新当前的 Todo 计划任务清单，并在终端渲染可视化列表"""
    global CURRENT_TODOS
    CURRENT_TODOS = todos

    if not todos:
        return "Todo 清单已清空。"

    rendered = ["\n\033[1;36m[TODO] [Agent 代办任务计划清单]\033[0m"]
    for idx, item in enumerate(todos, 1):
        content = item.get("content") or item.get("description") or ""
        status = item.get("status", "pending").lower()

        if status in ("completed", "done", "finished"):
            icon = "\033[32m[v]\033[0m"
            text_style = "\033[90m"
        elif status in ("in_progress", "running"):
            icon = "\033[33m[>]\033[0m"
            text_style = "\033[1;33m"
        else:
            icon = "\033[37m[ ]\033[0m"
            text_style = "\033[0m"

        rendered.append(f"  {idx}. {icon} {text_style}{content}\033[0m")

    print("\n".join(rendered))
    return f"Todo 清单成功更新，当前包含 {len(todos)} 项任务。"


# ── 2. 工具 Schema 与 路由注册 ──

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取本地文件的文本内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "相对工作目录的文件路径"},
                    "limit": {"type": "integer", "description": "可选：最多读取的行数"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "向本地文件全量写入内容。如果文件不存在会自动创建；如果已存在则覆盖。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "相对工作目录的文件路径"},
                    "content": {"type": "string", "description": "要写入文件的完整代码或文本内容"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "局部精确编辑/替换本地文件中的某段代码 (Search & Replace 模式)。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "相对工作目录的文件路径"},
                    "old_str": {"type": "string", "description": "文件中原有的、需要被替换的精确旧文本或代码块"},
                    "new_str": {"type": "string", "description": "用来替换旧文本的新文本或新代码块"}
                },
                "required": ["path", "old_str", "new_str"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "运行一个终端 / Shell 命令，例如运行 python 脚本、pytest 测试、pip 命令或任意 Git 版本控制命令 (如 git status, git diff, git commit 等)。",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "要执行的命令行指令"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_file_tree",
            "description": "获取当前工作区的文件与目录树结构骨架 (全局地图)。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "相对工作区的目录路径，默认为 '.'"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "todo_write",
            "description": "创建或更新 Agent 内部多步骤任务计划清单 (Todo List)。用于复杂任务拆解与进度状态追踪。",
            "parameters": {
                "type": "object",
                "properties": {
                    "todos": {
                        "type": "array",
                        "description": "Todo 任务项列表",
                        "items": {
                            "type": "object",
                            "properties": {
                                "content": {"type": "string", "description": "任务具体描述，如 '读取配置文件' 或 '修复单测报错'"},
                                "status": {
                                    "type": "string",
                                    "enum": ["pending", "in_progress", "completed"],
                                    "description": "任务当前状态: pending (待处理), in_progress (进行中), completed (已完成)"
                                }
                            },
                            "required": ["content", "status"]
                        }
                    }
                },
                "required": ["todos"]
            }
        }
    }
]

TOOL_HANDLERS = {
    "get_file_tree": run_get_file_tree,
    "read_file": run_read,
    "write_file": run_write,
    "edit_file": run_edit,
    "bash": run_bash,
    "todo_write": run_todo_write
}



