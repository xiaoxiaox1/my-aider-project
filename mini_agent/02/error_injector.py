"""
Mini Agent 02 工具失败提示词差异化注入引擎 (Tool Error Recovery Injector)
针对每一个工具 (read_file, write_file, edit_file, bash, get_file_tree) 的不同失败原因，
自动包装并注入专属的差异化系统强提醒与分析引导指令，彻底驱动大模型自愈纠错，绝不陷入死循环。
(GBK 终端兼容安全版)
"""

def is_tool_error(output: str) -> bool:
    """判断工具输出是否属于失败/拒绝状态"""
    if not isinstance(output, str):
        return False
    err_keywords = (
        "错误", "失败", "拒绝", "未通过", "未匹配",
        "Error", "Failed", "Refused", "SyntaxError", "NameError"
    )
    return any(k in output for k in err_keywords)


def format_tool_error_guidance(tool_name: str, args: dict, raw_output: str) -> str:
    """
    根据不同工具名称与具体失败原因，生成专属的差异化分析引导提示词 (GBK 安全版)
    """
    if not is_tool_error(raw_output):
        return raw_output

    path = args.get("path", "")
    cmd = args.get("command", "")

    # 1. read_file 专属失败引导
    if tool_name == "read_file":
        guidance = (
            f"[系统强提醒: read_file 读取文件失败!]\n"
            f"目标路径: '{path}'\n"
            f"失败原因:\n{raw_output}\n\n"
            f"[分析与自愈指令]:\n"
            f"1. 请先核对文件路径 '{path}' 是否拼写正确（是否遗漏了子目录前缀或文件扩展名）。\n"
            f"2. 若不确定文件具体位置，请先调起 `get_file_tree` 工具查询全仓库文件树结构。\n"
            f"3. 若文件属于二进制格式（如图片或压缩包），严禁再次发起文本读取。"
        )

    # 2. write_file 专属失败引导
    elif tool_name == "write_file":
        guidance = (
            f"[系统强提醒: write_file 全量写入文件被拒绝/失败!]\n"
            f"目标路径: '{path}'\n"
            f"失败原因:\n{raw_output}\n\n"
            f"[分析与自愈指令]:\n"
            f"1. 请仔细阅读上方的 Linter 校验报错，定位缺失的 `import` 模块（如 `import os`, `import math` 等）或语法错误的具体行号。\n"
            f"2. 在下一轮重新调用 `write_file` 时，务必在代码文件顶部补全缺失的 `import` 语句，并修正语法后重新写入。\n"
            f"3. 绝对禁止忽略 Linter 报错重复发送完全相同的坏代码。"
        )

    # 3. edit_file 专属失败引导
    elif tool_name == "edit_file":
        if "不存在" in raw_output:
            reason_hint = f"文件 '{path}' 在磁盘上并不存在！你无法直接编辑未创建的文件。"
            solution_hint = f"必须改用 `write_file(path='{path}', content=...)` 工具来创建该新文件，严禁再对不存在的文件调用 edit_file。"
        elif "未匹配" in raw_output:
            reason_hint = f"在 '{path}' 中未能匹配到你提供的 `old_str` (Search 块)。"
            solution_hint = f"请先调起 `read_file(path='{path}')` 查看该文件的最新真实代码，确保 `old_str` 与原文件代码 100% 精确一致（包含空格与换行）。"
        elif "Linter" in raw_output or "未通过" in raw_output:
            reason_hint = f"替换后的代码破坏了语法或遗漏了 `import` 导入语句。"
            solution_hint = f"请检查 `new_str`，确保替换后的代码符合 Python 语法且在文件顶部包含所有依赖的 `import` 语句。"
        else:
            reason_hint = raw_output
            solution_hint = "请重新检查参数并核对文件状态。"

        guidance = (
            f"[系统强提醒: edit_file 局部编辑被拒绝/失败!]\n"
            f"目标路径: '{path}'\n"
            f"失败原由: {reason_hint}\n\n"
            f"[分析与自愈指令]:\n"
            f"{solution_hint}"
        )

    # 4. bash 终端命令专属失败引导
    elif tool_name == "bash":
        guidance = (
            f"[系统强提醒: bash 命令执行失败或返回错误码!]\n"
            f"执行命令: `{cmd}`\n"
            f"终端报错信息:\n{raw_output}\n\n"
            f"[分析与自愈指令]:\n"
            f"1. 请仔细阅读上述终端输出中的错误 Traceback 堆栈信息，定位具体异常类型（如 ImportError, FileNotFoundError, SyntaxError, PermissionError 等）。\n"
            f"2. 针对捕获的具体报错修改代码或调整命令参数后重新运行。\n"
            f"3. 严禁盲目重复运行完全相同且未经修补的失败命令。"
        )

    # 5. get_file_tree 专属失败引导
    elif tool_name == "get_file_tree":
        guidance = (
            f"[系统强提醒: get_file_tree 目录树查询失败!]\n"
            f"失败原因:\n{raw_output}\n\n"
            f"[分析与自愈指令]: 请核对目录路径参数是否正确，默认传 '.' 表示获取根工作区结构。"
        )

    # 6. 其他通用工具失败引导
    else:
        guidance = (
            f"[系统强提醒: 工具 '{tool_name}' 执行失败!]\n"
            f"失败原因:\n{raw_output}\n\n"
            f"[分析与自愈指令]: 请仔细分析上述报错原因，调整工具参数后重试。"
        )

    return guidance
