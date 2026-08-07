"""
Mini Agent 02 工具集合模块
集成高容错 diff_engine 代码编辑引擎。
"""
import os
import subprocess
from pathlib import Path
from config import WORKDIR
from diff_engine import apply_search_replace

def safe_path(p: str) -> Path:
    """确保操作的文件路径在 WORKDIR 工作目录之内，防止路径遍历攻击"""
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"安全拒绝：路径企图越界访问 workspace 外部: {p}")
    return path

import mimetypes

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".pdf", ".zip", ".tar",
    ".gz", ".7z", ".rar", ".exe", ".dll", ".so", ".dylib", ".pyc", ".db",
    ".sqlite", ".bin", ".dat", ".wasm", ".class", ".o", ".obj"
}

def is_binary_file(file_path: Path) -> tuple[bool, str]:
    """判定文件是否属于二进制格式"""
    try:
        if not file_path.exists() or not file_path.is_file():
            return False, "文件不存在"
        size = file_path.stat().st_size
        if size == 0:
            return False, "空文件"

        with open(file_path, "rb") as f:
            raw = f.read(8192)

        if not raw:
            return False, "空文件"
        if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
            return False, "UTF-16 文本"
        if raw.startswith(b"\xef\xbb\xbf"):
            return False, "UTF-8 BOM 文本"

        for enc in ("utf-8", "gbk", "gb18030", "latin-1"):
            try:
                raw.decode(enc)
                null_count = raw.count(b"\x00")
                if null_count > 0 and (null_count / len(raw)) > 0.05:
                    return True, "二进制空字节比例高"
                return False, f"解码成功 ({enc})"
            except UnicodeDecodeError:
                continue

        return True, "非文本"
    except Exception as e:
        return True, str(e)


from git_undo import auto_git_checkpoint


def choose_fence(content: str) -> tuple[str, str]:
    """根据代码内容动态选择无冲突的 Fence 包围符 (避免内嵌 3 个反引号破坏 Prompt 结构)"""
    if "```" in content:
        if "````" not in content:
            return "````", "````"
        return "<code_block>", "</code_block>"
    return "```", "```"

# ── 1. 工具 Handler 实现 ──

def run_read(
    path: str,
    start_line: int = 1,
    end_line: int | None = None,
    max_lines: int = 250,
    max_chars: int = 15000,
    max_line_chars: int = 1000,
    show_line_numbers: bool = True
) -> str:
    """
    工业级切片与带行号/纯文本读取本地文件内容 (支持动态 Fence 隔离保护、零磁盘去重缓存与 GLOBAL_INDEXER 内存元数据)
    """
    try:
        target = safe_path(path)
        if not target.exists():
            return f"错误: 文件 {path} 不存在"
        if not target.is_file():
            return f"错误: {path} 是一个目录，非文件"

        rel_path = str(target.relative_to(WORKDIR)).replace("\\", "/")

        # 1. 优先查 GLOBAL_INDEXER 内存索引
        meta = GLOBAL_INDEXER.index.get(rel_path)
        if not meta:
            meta = GLOBAL_INDEXER.index_file(target)
            if meta:
                GLOBAL_INDEXER.index[rel_path] = meta

        if meta and meta.is_binary:
            return f"错误: 文件 {path} 已被全仓库元数据索引标记为二进制文件 ({meta.language}, 文件大小: {meta.size_bytes} 字节)，拒绝作为纯文本读取。"

        # -------------------------------------------------------------
        # 防线：读缓存去重拦截 (Read Deduplication Guard)
        # -------------------------------------------------------------
        if meta and meta.sha256 and rel_path in READ_CACHE:
            cached_sha, cached_show_ln, _ = READ_CACHE[rel_path]
            if cached_sha == meta.sha256 and cached_show_ln == show_line_numbers and start_line == 1 and end_line is None:
                print(f"\033[36m[Read Dedup] 文件 {path} 内容未变，触发去重拦截\033[0m")
                return (
                    f"=== 文件去重提示: {path} ===\n"
                    f"系统校验确认: 文件 {path} 自上轮读取以来 SHA256 未发生任何修改 ({meta.sha256})。"
                    f"该文件的完整最新内容已存在于上文对话中，无须重复读取。请直接使用已有的代码进行分析或编辑。"
                )

        # 2. 读取文本内容
        try:
            raw_content = target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                raw_content = target.read_text(encoding="gbk")
            except Exception:
                raw_content = target.read_text(encoding="utf-8", errors="replace")

        all_lines = raw_content.splitlines()
        total_lines = meta.total_lines if meta and meta.total_lines > 0 else len(all_lines)

        if total_lines == 0:
            return f"(文件 {path} 内容为空)"

        # 3. 切片计算
        s_line = max(1, start_line)
        if end_line is not None:
            e_line = min(total_lines, max(s_line, end_line))
            if e_line - s_line + 1 > max_lines:
                e_line = s_line + max_lines - 1
        else:
            e_line = min(total_lines, s_line + max_lines - 1)

        sliced_raw_lines = all_lines[s_line - 1 : e_line]

        # 4. 逐行字符预算与超长单行截断
        output_body = []
        char_count = 0
        actual_end_line = s_line - 1
        truncated_by_chars = False

        for curr_line_num, line_text in enumerate(sliced_raw_lines, start=s_line):
            if len(line_text) > max_line_chars:
                line_text = line_text[:max_line_chars] + f" ... [单行超长({len(line_text)}字符)已截断]"

            formatted_line = f"{curr_line_num:4d} | {line_text}" if show_line_numbers else line_text
            
            if char_count + len(formatted_line) + 1 > max_chars:
                truncated_by_chars = True
                break

            output_body.append(formatted_line)
            char_count += len(formatted_line) + 1
            actual_end_line = curr_line_num

        # 5. 结构化 Metadata Headers 与 Footers (带动态 Fence 包围保护)
        body_str = "\n".join(output_body)
        fence_open, fence_close = choose_fence(body_str)

        header = f"=== 文件: {path} (展示第 {s_line}~{actual_end_line} 行 / 共 {total_lines} 行) ==="
        wrapped_body = f"{fence_open}\n{body_str}\n{fence_close}"

        meta_info = [
            "\n[READ_METADATA]",
            f"filepath: {path}",
            f"start_line: {s_line}",
            f"end_line: {actual_end_line}",
            f"total_lines: {total_lines}",
            f"show_line_numbers: {show_line_numbers}",
            f"fence_used: '{fence_open}'",
            f"truncated: {'true' if (actual_end_line < total_lines or truncated_by_chars) else 'false'}"
        ]

        if truncated_by_chars:
            meta_info.append(f"truncation_reason: max_chars ({max_chars}) 字符预算达到上限")
            meta_info.append(f"next_start_line: {actual_end_line + 1}")
        elif actual_end_line < total_lines:
            meta_info.append(f"truncation_reason: max_lines ({max_lines}) 行数上限达到")
            meta_info.append(f"next_start_line: {actual_end_line + 1}")

        full_output = f"{header}\n{wrapped_body}\n" + "\n".join(meta_info)

        # 更新读取去重缓存
        if meta and meta.sha256:
            READ_CACHE[rel_path] = (meta.sha256, show_line_numbers, full_output)

        return full_output
    except Exception as e:
        return f"读取文件过程发生异常: {e}"

from diff_engine import apply_search_replace, validate_python_ast

def run_write(path: str, content: str) -> str:
    """全量创建或覆盖本地文件并同步更新内存元数据索引与读缓存 (带 Linter 缺失导入防线与 Git 自动备份)"""
    try:
        target = safe_path(path)

        # Python 文件全量写入前执行 Linter 缺失 import 校验防线
        if path.endswith(".py") or path.endswith(".pyi"):
            is_valid, linter_err = validate_python_ast(content, filepath=path)
            if not is_valid:
                return f"写入被拒绝：未通过 Python Linter 校验 (检测到未导入的模块或语法错误)。\n{linter_err}"

        # 写入磁盘前自动创建 Git Shadow Checkpoint 备份
        auto_git_checkpoint(reason=f"Before write_file to {path}")

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        
        # 运行时增量更新内存元数据索引
        new_meta = GLOBAL_INDEXER.index_file(target)
        if new_meta:
            GLOBAL_INDEXER.index[new_meta.path] = new_meta
            # 清理旧的读缓存以保证下次读取拿到最新修改
            READ_CACHE.pop(new_meta.path, None)

        return f"成功写入文件: {path} ({len(content)} 字符, 已通过 Linter 校验并创建 Git 备份)"
    except Exception as e:
        return f"写入文件错误: {e}"


def run_edit(path: str, old_str: str, new_str: str) -> str:
    """使用工业级 Diff Engine 进行高容错局部编辑，并同步更新内存元数据索引与读缓存 (带 Git 自动备份)"""
    try:
        target = safe_path(path)
        if not target.exists():
            return f"错误：文件 {path} 不存在！如果你想创建此新文件，必须调用 write_file(path, content) 工具进行创建，严禁对不存在的文件调用 edit_file。"
        content = target.read_text(encoding="utf-8")
        
        success, updated_or_err, tier_info = apply_search_replace(
            file_content=content,
            search_text=old_str,
            replace_text=new_str,
            filepath=path
        )
        
        if not success:
            return f"编辑被拒绝/失败：\n{updated_or_err}"
            
        # 编辑写盘前自动创建 Git Shadow Checkpoint 备份
        auto_git_checkpoint(reason=f"Before edit_file on {path}")

        target.write_text(updated_or_err, encoding="utf-8")
        
        # 运行时增量更新内存元数据索引
        new_meta = GLOBAL_INDEXER.index_file(target)
        if new_meta:
            GLOBAL_INDEXER.index[new_meta.path] = new_meta
            # 清理旧的读缓存以保证下次读取拿到最新修改
            READ_CACHE.pop(new_meta.path, None)

        return f"成功编辑文件: {path} (匹配模式: {tier_info}, 已创建 Git 备份并同步内存索引)"
    except Exception as e:
        return f"编辑文件过程出现异常: {e}"
def run_bash(command: str) -> str:
    """在工作目录下运行终端命令"""
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

def run_get_file_tree(path: str = '.'):
    """获取工作区的目录树骨架地图"""
    try:
        target = safe_path(path)
        if not target.exists():
            return f"错误: 目录 {path} 不存在"
        ignore_dir = {".git", "__pycache__", ".venv", ".idea"}
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
            "description": "读取本地文件的文本内容 (支持多维字符/行号预算控制，可开启/关闭行号前缀，附带结构化 Metadata)。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "相对工作目录的文件路径"},
                    "start_line": {"type": "integer", "description": "可选：启始行号 (1-indexed，默认为 1)"},
                    "end_line": {"type": "integer", "description": "可选：结束行号 (包含)"},
                    "show_line_numbers": {"type": "boolean", "description": "可选：是否显示行号前缀。默认为 True。若需要精准复制原始内容生成 Edit Block，可设为 False"}
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
            "description": "局部精确编辑/替换本地文件中的某段代码 (Search & Replace 模式，具备高容错对齐与 AST 语法安全防线)。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "相对工作目录的文件路径"},
                    "old_str": {"type": "string", "description": "文件中原有的、需要被替换的旧代码块 (Search Block)"},
                    "new_str": {"type": "string", "description": "用来替换旧代码块的新代码块 (Replace Block)"}
                },
                "required": ["path", "old_str", "new_str"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "运行一个终端 / Shell 命令，例如运行 python 脚本、pytest 测试、pip/uv 命令或任意 Git 版本控制命令 (如 git status, git diff, git commit 等)。",
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
