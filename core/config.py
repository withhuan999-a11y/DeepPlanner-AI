import os
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()
API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not API_KEY:
    raise ValueError("未找到 DEEPSEEK_API_KEY，请检查 .env 文件。")

# 初始化全局可用的 OpenAI 客户端
client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")