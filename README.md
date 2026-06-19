📌 项目简介

DeepPlanner AI 是一个基于大语言模型 (LLM) 与github站内非常好用的Agent-Reach(https://github.com/Panniantong/Agent-Reach)以及Opencil工具  构建的防坑反营销智能体 (Agent)。

系统坚持“正文是用来表演的，评论区才是用来避坑的”的极客理念。通过底层物理穿透社交平台（如小红书）的真实评论区，结合大模型的意图路由与天气感知，为你提炼出绝对客观、去水军的专属旅行攻略与产品评测数据。

✨ 核心特性

🛡️ 评论区法医：强制大模型进行脱水分析，剥离情绪化软广，精准提取评论区的“排雷警告”。

🤖 动态意图与原生 Agent：

旅游规划：基于 ReAct 架构，大模型自主调用外部 API 获取当地实时天气，并根据天气（如高温/暴雨）动态调整行程。

产品评测：强制进行“舆情量化分析”，输出真实的网友情感百分比（如：50%性价比高，25%吐槽散热）。

⚡ 双模决策引擎：支持「🌐 深度搜索」与「💬 记忆连聊」无缝切换。利用记忆窗口实现极速条件修改，拒绝冗余抓取。

🛠️ 模块化架构：核心业务与工具链（Tools）物理隔离，支持未来无缝扩展地图、比价等新工具。

📂 项目结构

DeepPlanner/
├── main.py               # 轻量级网关：FastAPI 路由入口
├── index.html            # 极简前端：React 18 + Tailwind 单文件挂载
├── core/                 # 核心大脑
│   ├── config.py         # 环境与配置
│   ├── scraper.py        # 异步并发底层爬虫
│   └── agent.py          # 智能体决策中枢与 ReAct 循环
└── tools/                # 工具注册中心
    ├── __init__.py       # 工具派发器
    └── weather.py        # 天气 API 原生接入


🚀 快速上手

1. 环境准备
确保已安装 Python 3.9+，并安装以下依赖：

pip install fastapi uvicorn pydantic openai python-dotenv uapi-sdk-python


(注：底层数据抓取依赖本地 OpenCLI 守护进程的支持)

2. 配置密钥
在根目录创建 .env 文件，填入你的 API Key：

API_KEY=sk-xxxxxx...


3. 启动服务

python main.py


浏览器打开 http://127.0.0.1:8000 即可体验。

免责声明：本项目仅供技术探索与个人学习使用，旨在提升信息获取的信噪比。
