"""
Mini Agent 02 通用代码 Linter 与全量模块/符号检测引擎 (Linter Engine)
动态识别 Python 官方 300+ 标准库模块、所有已安装第三方包以及当前工作区本地 Python 模块。
告别硬编码白名单，提供全量未定义符号与缺失 import 的自动拦截能力。
"""
import ast
import sys
import pkgutil
import builtins
from pathlib import Path
from config import WORKDIR

def get_all_known_modules() -> set[str]:
    """
    动态获取当前 Python 环境与工作区中所有可用的模块名称列表
    (涵盖 300+ 官方标准库、已安装第三方包如 requests/numpy/pytest、工作区本地 .py 模块)
    """
    modules = set()

    # 1. 官方标准库模块 (Python 3.10+ 原生提供 300+ 标准库模块)
    if hasattr(sys, "stdlib_module_names"):
        modules.update(sys.stdlib_module_names)
    else:
        modules.update(sys.builtin_module_names)

    # 2. 已安装的第三方包 (通过 pkgutil 动态扫描当前 Python 环境)
    try:
        for m in pkgutil.iter_modules():
            modules.add(m.name)
    except Exception:
        pass

    # 3. 当前工作区中的本地 Python 模块 (.py 文件与包目录)
    try:
        if WORKDIR.exists():
            for p in WORKDIR.glob("*.py"):
                modules.add(p.stem)
            for p in WORKDIR.iterdir():
                if p.is_dir() and (p / "__init__.py").exists():
                    modules.add(p.name)
    except Exception:
        pass

    return modules


BUILTIN_NAMES = set(dir(builtins)) | {
    "__name__", "__file__", "__doc__", "__all__", "__builtins__", "__self__"
}


class ASTImportChecker(ast.NodeVisitor):
    """AST 访问者：深度收集代码中的 Import 语句、定义名称、异常变量与使用的模块"""
    def __init__(self):
        self.imported_names: set[str] = set()
        self.defined_names: set[str] = set()
        self.used_names: list[tuple[str, int]] = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name.split('.')[0]
            self.imported_names.add(name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imported_names.add(name)
            if node.module:
                self.imported_names.add(node.module.split('.')[0])
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.defined_names.add(node.name)
        for arg in node.args.args:
            self.defined_names.add(arg.arg)
        if node.args.kwarg:
            self.defined_names.add(node.args.kwarg.arg)
        if node.args.vararg:
            self.defined_names.add(node.args.vararg.arg)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.defined_names.add(node.name)
        for arg in node.args.args:
            self.defined_names.add(arg.arg)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self.defined_names.add(node.name)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        if node.name:
            self.defined_names.add(node.name)
        self.generic_visit(node)

    def visit_Lambda(self, node: ast.Lambda):
        for arg in node.args.args:
            self.defined_names.add(arg.arg)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Store):
            self.defined_names.add(node.id)
        elif isinstance(node.ctx, ast.Load):
            self.used_names.append((node.id, node.lineno))
        self.generic_visit(node)


def check_python_linter(code: str, filepath: str = "") -> tuple[bool, list[str]]:
    """
    检查 Python 代码的语法与缺失 import 错误 (全量动态模块版本)
    """
    # 1. 尝试使用 Pyflakes
    try:
        import pyflakes.api
        import pyflakes.reporter
        import io

        warnings_io = io.StringIO()
        reporter = pyflakes.reporter.Reporter(warnings_io, warnings_io)
        pyflakes.api.check(code, filepath or "string", reporter=reporter)
        output = warnings_io.getvalue().strip()
        if output:
            errors = [line for line in output.splitlines() if "undefined name" in line]
            if errors:
                return False, errors
    except ImportError:
        pass

    # 2. 动态获取当前环境与工作区中的已知模块表
    known_modules = get_all_known_modules()

    # 3. 静态语法树解析
    try:
        tree = ast.parse(code, filename=filepath or "<string>")
    except SyntaxError as e:
        return False, [f"SyntaxError 在第 {e.lineno} 行: {e.msg}"]

    checker = ASTImportChecker()
    checker.visit(tree)

    missing_imports = []
    seen = set()

    for name, lineno in checker.used_names:
        if (
            name not in BUILTIN_NAMES
            and name not in checker.imported_names
            and name not in checker.defined_names
            and name not in seen
        ):
            seen.add(name)
            # 优先精准定位缺失的包/模块导入错误
            if name in known_modules:
                missing_imports.append(f"第 {lineno} 行: 检测到使用了未导入的模块/包 '{name}'，缺少 'import {name}' 或 'from {name} import ...'")

    if missing_imports:
        return False, missing_imports

    return True, []

