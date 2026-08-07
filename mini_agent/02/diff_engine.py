"""
Mini Agent 02 工业级高容错代码编辑引擎 (Diff Engine)
包含三阶渐进式模糊匹配 (Exact -> Normalized -> Indentation Auto-Alignment) 及 AST 语法防御。
"""
import ast
import re


def normalize_line_endings(text: str) -> str:
    """归一化换行符为 \\n"""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def strip_trailing_spaces(lines: list[str]) -> list[str]:
    """去除每一行末尾的无意义空白字符"""
    return [line.rstrip() for line in lines]


def get_indentation(line: str) -> str:
    """提取某行的前导缩进（空格或 Tab）"""
    match = re.match(r"^(\s*)", line)
    return match.group(1) if match else ""


from linter import check_python_linter


def validate_python_ast(content: str, filepath: str = "") -> tuple[bool, str | None]:
    """使用 Python 官方 AST 及 Linter 检查代码语法与缺失 import 完整性"""
    is_ok, errs = check_python_linter(content, filepath=filepath)
    if not is_ok:
        return False, "\n".join(errs)
    return True, None



def apply_search_replace(
    file_content: str,
    search_text: str,
    replace_text: str,
    filepath: str | None = None
) -> tuple[bool, str, str | None]:
    """
    高容错 Search-Block 代码替换核心逻辑
    :param file_content: 原文件完整文本
    :param search_text: 需要被替换的旧代码块 (Search Block)
    :param replace_text: 用于替换的新代码块 (Replace Block)
    :param filepath: 可选的文件路径，用于判断是否触发 AST 语法校验
    :return: (is_success, updated_content_or_error_msg, tier_used_info)
    """
    if not search_text:
        return False, "Search 代码块不能为空", None

    norm_file_content = normalize_line_endings(file_content)
    norm_search_text = normalize_line_endings(search_text)
    norm_replace_text = normalize_line_endings(replace_text)

    # -------------------------------------------------------------
    # Tier 1: 完全精确匹配 (Exact Match)
    # -------------------------------------------------------------
    if norm_search_text in norm_file_content:
        updated = norm_file_content.replace(norm_search_text, norm_replace_text, 1)
        tier_used = "Tier 1 (Exact Match)"
        
        # AST 语法防线
        if filepath and (filepath.endswith(".py") or filepath.endswith(".pyi")):
            is_valid, ast_err = validate_python_ast(updated)
            if not is_valid:
                return False, f"修改拒绝：Tier 1 替换后未通过 Python AST 语法校验。\n{ast_err}", tier_used
                
        return True, updated, tier_used

    # 按行切割准备进行高级归一化/缩进匹配
    file_lines = norm_file_content.split("\n")
    search_lines = norm_search_text.split("\n")
    replace_lines = norm_replace_text.split("\n")

    search_count = len(search_lines)

    # -------------------------------------------------------------
    # Tier 2: 尾部空白归一化匹配 (Trailing Whitespace & Line-ending Match)
    # -------------------------------------------------------------
    stripped_search = strip_trailing_spaces(search_lines)
    stripped_file = strip_trailing_spaces(file_lines)

    for i in range(len(file_lines) - search_count + 1):
        file_sub_lines = stripped_file[i : i + search_count]
        if file_sub_lines == stripped_search:
            # 找到匹配的行范围 [i, i + search_count]
            updated_lines = file_lines[:i] + replace_lines + file_lines[i + search_count:]
            updated = "\n".join(updated_lines)
            tier_used = "Tier 2 (Normalized Trailing Whitespace Match)"

            if filepath and (filepath.endswith(".py") or filepath.endswith(".pyi")):
                is_valid, ast_err = validate_python_ast(updated)
                if not is_valid:
                    return False, f"修改拒绝：Tier 2 替换后未通过 Python AST 语法校验。\n{ast_err}", tier_used

            return True, updated, tier_used

    # -------------------------------------------------------------
    # Tier 3: 忽略前导缩进 & 相对缩进自动对齐 (Indentation Auto-Alignment Match)
    # -------------------------------------------------------------
    clean_search = [line.strip() for line in search_lines]
    
    # 过滤掉 Search 块首尾空行影响
    first_non_empty_search = next((s for s in clean_search if s), "")
    
    if first_non_empty_search:
        for i in range(len(file_lines) - search_count + 1):
            file_sub_clean = [line.strip() for line in file_lines[i : i + search_count]]
            if file_sub_clean == clean_search:
                # 找到符合结构的行！开始计算目标代码基准前导缩进
                target_base_indent = get_indentation(file_lines[i])
                search_base_indent = get_indentation(search_lines[0])

                # 自动对齐 Replace 代码块的缩进
                aligned_replace_lines = []
                for r_line in replace_lines:
                    if not r_line.strip():
                        aligned_replace_lines.append("")
                    else:
                        r_indent = get_indentation(r_line)
                        if r_indent.startswith(search_base_indent):
                            relative_indent = r_indent[len(search_base_indent):]
                        else:
                            relative_indent = r_indent
                        aligned_replace_lines.append(target_base_indent + relative_indent + r_line.lstrip())

                updated_lines = file_lines[:i] + aligned_replace_lines + file_lines[i + search_count:]
                updated = "\n".join(updated_lines)
                tier_used = "Tier 3 (Indentation Auto-Alignment Match)"

                if filepath and (filepath.endswith(".py") or filepath.endswith(".pyi")):
                    is_valid, ast_err = validate_python_ast(updated)
                    if not is_valid:
                        return False, f"修改拒绝：Tier 3 替换并修正缩进后未通过 Python AST 语法校验。\n{ast_err}", tier_used

                return True, updated, tier_used

    # 如果所有 Tier 均未匹配，生成友好的排查提示
    error_detail = (
        f"在目标文件中未匹配到指定的 Search 块 (尝试了 Tier 1/2/3 算法均失败)。\n"
        f"Search 块行数: {search_count} 行\n"
        f"提示: 请检查 Search 块中的代码文本是否属于该文件的真实代码片段。"
    )
    return False, error_detail, None
