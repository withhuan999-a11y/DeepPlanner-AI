import os
import subprocess
import json
import re
import asyncio
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise ValueError("未找到 DEEPSEEK_API_KEY，请检查 .env 文件。")

client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
app = FastAPI()

# ==========================================
# 核心数据模型
# ==========================================
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    query: str
    history: list[Message]
    use_deep_search: bool

# ==========================================
# 底层抓取逻辑
# ==========================================
def run_cli_command(command: str) -> str:
    try:
        print(f"[CLI执行] {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
        return result.stdout
    except Exception as e:
        return f"Error: {str(e)}"

def extract_urls_with_llm(raw_search_text: str, max_count: int = 5) -> list:
    prompt = f"""
    以下是命令行抓取到的小红书搜索结果文本。
    请从中提取出最多 {max_count} 个具体帖子的完整 URL。
    【极度重要】：URL 必须包含完整的参数（如 ?xsec_token=...），绝不能截断！
    请仅返回一个合法的 JSON 格式的字符串数组。
    
    原始数据：
    {raw_search_text[:3000]}
    """
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        content = response.choices[0].message.content.strip()
        content = re.sub(r"```json\n|\n```|```", "", content).strip()
        urls = json.loads(content)
        return urls if isinstance(urls, list) else []
    except Exception as e:
        print(f"[错误] URL提取失败，使用降级正则: {e}")
        urls = re.findall(r'(https?://[^\s<>"\']+xiaohongshu\.com/explore/\w+(?:\?xsec_token=[a-zA-Z0-9_-]+(?:&[a-zA-Z0-9_-]+=[^&\s]*)*)?)', raw_search_text)
        return list(set(urls))[:max_count]

async def perform_deep_search(query: str) -> str:
    print(f"\n--- 开始深度侦察: {query} ---")
    search_command = f'opencli xiaohongshu search "{query}"'
    raw_search = await asyncio.to_thread(run_cli_command, search_command)
    
    if not raw_search.strip():
        return "未能抓取到任何搜索结果，可能是网络或风控问题。"

    urls = await asyncio.to_thread(extract_urls_with_llm, raw_search, 4)
    if not urls:
        return "未能提取到有效的帖子链接。"

    compiled_data = ""
    valid_count = 0
    for idx, url in enumerate(urls, 1):
        safe_url = f'"{url}"'
        note_command = f'opencli xiaohongshu note {safe_url}'
        note_data = await asyncio.to_thread(run_cli_command, note_command)
        
        if len(note_data.strip()) > 100:
            valid_count += 1
            compiled_data += f"\n\n--- 帖子 {idx} ({url}) ---\n{note_data}\n--- 结束 ---\n"
            
    if valid_count == 0:
        return "警告：抓取到的所有帖子均无有效内容（触发了反爬）。"
        
    return compiled_data

# ==========================================
# API 路由
# ==========================================
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    messages = [{"role": m.role, "content": m.content} for m in request.history]
    
    if request.use_deep_search:
        scraped_context = await perform_deep_search(request.query)
        
        system_prompt = f"""
        你是“全能生活规划师 & 冷酷反营销侦察兵”。
        用户的诉求是：【{request.query}】。
        
        这是我为你从网上实时抓取的最新数据（包含多篇帖子的正文与真实评论）：
        {scraped_context}
        
        你的核心任务（请一步步思考并按 Markdown 格式输出）：
        1. 🕵️‍♂️ 刺客排雷：首先审视数据，把所有的“软广、水军、坑点、避雷警告”提炼出来，放在最前面警示用户。如果评论区有大量吐槽，必须标红警告。
        2. 🗺️ 宗师级规划：基于筛选后的真实、健康的数据，结合你自身强大的知识库，为用户输出一份极具结构感、可执行的“定制化攻略/计划”。
           （例如：包含时间线的行程表、美食打卡地图、穿搭建议等。使用表格、粗体、列表来优化阅读体验。）
        3. 💡 绝密贴士：给出1-2个只有本地人/内行才知道的额外建议。
        
        语气要求：专业、干脆、有极客感，不需要过分客气。
        """
        current_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.query}
        ]
    else:
        system_prompt = """
        你是全能的规划助手，请基于我们之前的对话记忆，回答用户的后续追问。
        如果用户的要求是对先前的攻略进行修改（如换一家餐厅、缩短时间），请直接给出修改后的精确方案，不用重复全部内容。
        """
        current_messages = [{"role": "system", "content": system_prompt}] + messages + [{"role": "user", "content": request.query}]

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=current_messages,
            temperature=0.4,
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        return {"reply": f"❌ 大模型处理失败: {str(e)}"}

# ==========================================
# 静态页面挂载
# ==========================================
@app.get("/")
async def get_index():
    return FileResponse("index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)