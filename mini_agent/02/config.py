import os
import subprocess
from pathlib import Path
from prompts import build_system_prompt

# LLM 独立专属工作目录 (隔离 Agent 自身代码与大模型工作区)
WORKDIR = Path("E:/code/my-agent-repo/llm_work").resolve()

# 确保目标目录存在
WORKDIR.mkdir(parents=True, exist_ok=True)

def init_git_workspace():
    """自动确保工作区初始化为 Git 仓库并配置默认身份信息"""
    git_dir = WORKDIR / ".git"
    if not git_dir.exists():
        subprocess.run(["git", "init"], cwd=WORKDIR, capture_output=True, text=True)
    
    r_name = subprocess.run(["git", "config", "user.name"], cwd=WORKDIR, capture_output=True, text=True)
    if not r_name.stdout.strip():
        subprocess.run(["git", "config", "user.name", "MiniAgent"], cwd=WORKDIR, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.email", "agent@local"], cwd=WORKDIR, capture_output=True, text=True)

init_git_workspace()

# 本地 LLM 配置
BASE_URL = os.getenv("LOCAL_LLM_URL", "http://10.128.7.115:3101/v1")
MODEL = os.getenv("LOCAL_LLM_MODEL", "Qwen3-30B-A3B-FP8")
API_KEY = os.getenv("LOCAL_LLM_KEY", "ollama")

# 动态构建注入了环境元数据的全局 SYSTEM_PROMPT
SYSTEM_PROMPT = build_system_prompt(WORKDIR, MODEL)
