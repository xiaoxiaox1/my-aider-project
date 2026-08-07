"""
Mini Agent 02 全仓库文件元数据索引库 (Workspace File Indexer)
启动时快速并发/递归扫描工作区文件，建立内存元数据索引，自动标记过滤二进制文件。
"""
import os
import time
import hashlib
from pathlib import Path
from dataclasses import dataclass
from tools import is_binary_file, safe_path
from config import WORKDIR

IGNORE_DIRS = {
    ".git", "__pycache__", ".venv", "venv", "node_modules",
    ".idea", ".vscode", "dist", "build", ".next", ".mypy_cache"
}

@dataclass
class FileMetadata:
    path: str           # 相对路径 (如 "src/main.py")
    size_bytes: int     # 字节大小
    total_lines: int    # 代码总行数 (文本文件)
    mtime: float        # 最后修改时间戳
    language: str       # 编程语言分类 (如 "python", "javascript")
    is_binary: bool     # 是否为二进制文件 (自动过滤)
    sha256: str         # 摘要哈希 (用于增量更新)


class WorkspaceFileIndexer:
    def __init__(self, workdir: Path = WORKDIR):
        self.workdir = workdir
        self.index: dict[str, FileMetadata] = {}

    def detect_language(self, path: Path) -> str:
        """根据文件扩展名识别编程语言或文本类型"""
        ext = path.suffix.lower()
        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript-react",
            ".jsx": "javascript-react",
            ".html": "html",
            ".css": "css",
            ".json": "json",
            ".md": "markdown",
            ".yml": "yaml",
            ".yaml": "yaml",
            ".toml": "toml",
            ".sh": "bash",
            ".ps1": "powershell",
            ".rs": "rust",
            ".go": "go",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c-header"
        }
        return lang_map.get(ext, "text" if not ext else ext[1:])

    def index_file(self, full_path: Path) -> FileMetadata | None:
        """索引单个文件的元数据对象"""
        try:
            rel_path = str(full_path.relative_to(self.workdir)).replace("\\", "/")
            stat = full_path.stat()
            size = stat.st_size
            mtime = stat.st_mtime

            # 1. 检测二进制文件并进行排除/标记
            is_bin, _ = is_binary_file(full_path)
            lang = self.detect_language(full_path)

            if is_bin:
                return FileMetadata(
                    path=rel_path,
                    size_bytes=size,
                    total_lines=0,
                    mtime=mtime,
                    language="binary",
                    is_binary=True,
                    sha256=""
                )

            # 2. 读取文本计算代码行数与 SHA256
            try:
                content = full_path.read_text(encoding="utf-8", errors="replace")
                lines = len(content.splitlines())
                sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
            except Exception:
                lines = 0
                sha256 = ""

            return FileMetadata(
                path=rel_path,
                size_bytes=size,
                total_lines=lines,
                mtime=mtime,
                language=lang,
                is_binary=False,
                sha256=sha256
            )
        except Exception:
            return None

    def scan_workspace(self) -> dict[str, FileMetadata]:
        """全量扫描全工作区所有文件并构建内存索引表"""
        start_time = time.time()
        new_index = {}
        text_count = 0
        bin_count = 0
        total_code_lines = 0

        for root, dirs, files in os.walk(self.workdir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for file_name in files:
                full_path = Path(root) / file_name
                meta = self.index_file(full_path)
                if meta:
                    new_index[meta.path] = meta
                    if meta.is_binary:
                        bin_count += 1
                    else:
                        text_count += 1
                        total_code_lines += meta.total_lines

        self.index = new_index
        elapsed = time.time() - start_time
        print(f"\033[32m[Workspace Indexer] 全仓库元数据索引已建立 (耗时 {elapsed:.3f}s):\033[0m")
        print(f"   文本源文件: {text_count} 个 (共 {total_code_lines} 行代码)")
        print(f"   二进制文件: {bin_count} 个 (已标记过滤)")
        return self.index

    def get_summary(self) -> str:
        """生成供大模型或终端查看的全仓库元数据概览"""
        if not self.index:
            self.scan_workspace()


        text_files = [m for m in self.index.values() if not m.is_binary]
        bin_files = [m for m in self.index.values() if m.is_binary]
        total_lines = sum(m.total_lines for m in text_files)

        res = [
            f"全仓库元数据概览 (工作区: {self.workdir.name}):",
            f"- 源文件总数: {len(text_files)} 个文本文件 | 二进制过滤文件: {len(bin_files)} 个",
            f"- 代码总行数: {total_lines} 行\n",
            "主要源文件清单:"
        ]
        for m in sorted(text_files, key=lambda x: x.path):
            res.append(f"  [SRC] {m.path:<35} | {m.language:<10} | {m.total_lines:4d} 行 | {m.size_bytes} 字节")

        if bin_files:
            res.append("\n二进制过滤文件清单 (禁止文本读取):")
            for m in sorted(bin_files, key=lambda x: x.path):
                res.append(f"  [BIN] {m.path:<35} | binary     | {m.size_bytes} 字节")


        return "\n".join(res)


# 创建全局单例索引器
GLOBAL_INDEXER = WorkspaceFileIndexer()
