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
            "description": "运行一个终端 / Shell 命令，例如运行 python 脚本、pytest 测试、pip 命令或查看目录内容。",
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
    }
]

TOOL_HANDLERS = {
    "get_file_tree": run_get_file_tree,
    "read_file": run_read,
    "write_file": run_write,
    "edit_file": run_edit,
    "bash": run_bash
}
