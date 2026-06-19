import subprocess
import json
import re
import asyncio
from core.config import client

def run_cli_command(command: str) -> str:
    """执行本地终端命令"""
    try:
        print(f"[CLI执行] {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
        return result.stdout
    except Exception as e:
        return f"Error: {str(e)}"

def extract_urls_with_llm(raw_search_text: str, max_count: int = 5) -> list:
    """使用 LLM 提取合法的帖子 URL"""
    prompt = f"""
    以下是命令行抓取到的小红书搜索结果文本。请提取最多 {max_count} 个帖子的完整 URL。
    【极度重要】：URL 必须包含完整的参数（如 ?xsec_token=...），绝不能截断！
    请仅返回合法的 JSON 字符串数组。
    原始数据：{raw_search_text[:3000]}
    """
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        content = response.choices[0].message.content.strip()
        content = re.sub(r"```json\n|\n```|```", "", content).strip()
        return json.loads(content)
    except Exception:
        urls = re.findall(r'(https?://[^\s<>"\']+xiaohongshu\.com/explore/\w+(?:\?xsec_token=[a-zA-Z0-9_-]+(?:&[a-zA-Z0-9_-]+=[^&\s]*)*)?)', raw_search_text)
        return list(set(urls))[:max_count]

async def perform_deep_search(query: str) -> str:
    """执行完整的深度侦察流程"""
    print(f"\n--- 开始底层侦察: {query} ---")
    search_command = f'opencli xiaohongshu search "{query}"'
    raw_search = await asyncio.to_thread(run_cli_command, search_command)
    
    if not raw_search.strip():
        return "未能抓取到结果，可能触发风控。"

    urls = await asyncio.to_thread(extract_urls_with_llm, raw_search, 4)
    if not urls:
        return "未能提取到有效的帖子链接。"

    compiled_data = ""
    for idx, url in enumerate(urls, 1):
        safe_url = f'"{url}"'
        note_command = f'opencli xiaohongshu note {safe_url}'
        note_data = await asyncio.to_thread(run_cli_command, note_command)
        if len(note_data.strip()) > 100:
            compiled_data += f"\n\n--- 帖子 {idx} ({url}) ---\n{note_data}\n--- 结束 ---\n"
            
    return compiled_data if compiled_data else "抓取的数据为空。"