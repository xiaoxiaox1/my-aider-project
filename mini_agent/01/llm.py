import json
import urllib.request
import urllib.error
from config import BASE_URL, MODEL, API_KEY
from tools import TOOLS

def call_local_llm(messages: list) -> tuple[dict | None, str]:
    """纯粹的 LLM HTTP 通信模块：负责将 messages 发送给远端/本地大模型，并返回 (choice_msg, finish_reason)"""
    url = f"{BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    payload = {
        "model": MODEL,
        "messages": messages,
        "tools": TOOLS,
        "tool_choice": "auto",
        "temperature": 0.2
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            choice = data["choices"][0]
            return choice["message"], choice.get("finish_reason", "stop")
    except Exception as e:
        print(f"\n\033[31m[LLM 请求失败]\033[0m {e}")
        # 失败时安全返回 Error 说明，防止解包崩溃
        err_msg = {"role": "assistant", "content": f"错误：调用本地 LLM 服务失败: {e}"}
        return err_msg, "error"
