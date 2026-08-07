"""
Mini Agent 本地物理环境探测模块 (Environment Detector)
"""
import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path
from datetime import datetime


def detect_environment(workdir: Path) -> dict:
    os_name = f"{platform.system()} {platform.release()} ({platform.machine()})"
    shell_raw = os.environ.get("SHELL") or os.environ.get("COMSPEC", "cmd.exe")
    if "powershell" in shell_raw.lower():
        shell_desc = f"PowerShell ({shell_raw})"
    elif "cmd.exe" in shell_raw.lower():
        shell_desc = f"Windows Command Prompt ({shell_raw})"
    else:
        shell_desc = shell_raw
        
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")
    if not editor:
        term_program = os.environ.get("TERM_PROGRAM", "")
        if "vscode" in term_program.lower():
            editor = "VS Code"
        elif "antigravity" in term_program.lower():
            editor = "Antigravity IDE"
        elif platform.system() == "Windows":
            editor = "Notepad / VS Code"
        else:
            editor = "Vim / Nano"

    tz_info = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z (UTC%z)")
    
    git_info = "Not a git repository"
    try:
        r_branch = subprocess.run(["git", "branch", "--show-current"], cwd=workdir, capture_output=True, text=True, timeout=2)
        branch = r_branch.stdout.strip() or "main"
        r_status = subprocess.run(["git", "status", "--porcelain"], cwd=workdir, capture_output=True, text=True, timeout=2)
        changes = len(r_status.stdout.strip().splitlines()) if r_status.stdout.strip() else 0
        git_info = f"Branch '{branch}' ({changes} modified files)" if changes > 0 else f"Branch '{branch}' (clean)"
    except Exception:
        pass

    py_ver = f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    has_uv_cli = shutil.which("uv") is not None
    root_dir = workdir.parent if workdir.parent.exists() else workdir
    has_uv_lock = (workdir / "uv.lock").exists() or (root_dir / "uv.lock").exists()
    has_pyproject = (workdir / "pyproject.toml").exists() or (root_dir / "pyproject.toml").exists()

    if has_uv_cli and (has_uv_lock or has_pyproject):
        package_manager = "uv (已检测到 uv.lock / pyproject.toml，请统一使用 'uv add <pkg>')"
        uses_uv = True
    elif has_uv_cli:
        package_manager = "uv (已安装 uv CLI，优先使用 'uv add <pkg>')"
        uses_uv = True
    else:
        package_manager = "pip (标准 pip install)"
        uses_uv = False

    return {
        "os": os_name,
        "shell": shell_desc,
        "editor": editor,
        "timezone": tz_info,
        "git": git_info,
        "python": py_ver,
        "package_manager": package_manager,
        "uses_uv": uses_uv
    }
