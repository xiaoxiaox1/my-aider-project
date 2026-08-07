"""
Mini Agent 02 Git 影子检查点与一键 /undo 撤销回滚引擎 (Git Undo Engine)
在 write_file / edit_file 之前自动做无损 Git Checkpoint。
用户随时可在命令行输入 /undo 一键回滚到修改前的完好状态！
"""
import subprocess
from pathlib import Path
from config import WORKDIR


def is_git_repo(workdir: Path = WORKDIR) -> bool:
    """检查工作区是否为一个 Git 仓库"""
    return (workdir / ".git").exists()


def auto_git_checkpoint(reason: str = "Agent auto checkpoint") -> bool:
    """在 Agent 写入/编辑文件前自动做 Git 暂存提交 Checkpoint"""
    if not is_git_repo():
        return False
    try:
        # 默默添加未暂存的修改并做一个 checkpoint commit
        subprocess.run(
            ["git", "add", "."],
            cwd=WORKDIR,
            capture_output=True,
            text=True
        )
        r = subprocess.run(
            ["git", "commit", "-m", f"[MiniAgent Checkpoint] {reason}"],
            cwd=WORKDIR,
            capture_output=True,
            text=True
        )
        return r.returncode == 0
    except Exception:
        return False


def undo_last_checkpoint() -> str:
    """运行一键撤销命令，回滚最近一次 Agent 修改"""
    if not is_git_repo():
        return "⚠️ 当前工作区未开启 Git 版本控制，无法使用一键 /undo 回滚功能。"

    try:
        # 查看上一条 commit 历史
        r_log = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%s"],
            cwd=WORKDIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        last_commit_msg = r_log.stdout.strip()

        # 回滚最近一次提交
        r_reset = subprocess.run(
            ["git", "reset", "--hard", "HEAD~1"],
            cwd=WORKDIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        if r_reset.returncode == 0:
            return f"\033[32m[Undo 成功] 已成功一键撤销上一轮修改！\n最近回滚记录: '{last_commit_msg}'\033[0m"
        else:
            # 尝试撤销本地未提交修改
            subprocess.run(["git", "checkout", "."], cwd=WORKDIR, capture_output=True)
            return "\033[32m[Undo 成功] 已清空并撤销当前未提交的本地修改。\033[0m"
    except Exception as e:
        return f"撤销过程发生异常: {e}"
