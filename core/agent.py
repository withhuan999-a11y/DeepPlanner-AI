import json
import asyncio
from typing import List, Dict, Optional
from core.config import client
from tools import AVAILABLE_TOOLS, dispatch_tool

async def chat_with_agent(query: str, history: Optional[List[Dict]] = None, context: str = "", tools_enabled: bool = False) -> str:
    """处理与大模型的完整对话流及 Tool Calling 循环"""
    messages = history or []
    
    if tools_enabled and context:
        system_prompt = f"""
        你是“全能防坑旅行规划师与产品分析师”。用户的诉求是：【{query}】。
        
        基于以下抓取的互联网真实数据：
        {context}
        
        任务规范（请严格遵循意图分支）：
        1. 若诉求为【旅行/路线规划】：如果涉及具体城市，请务必调用 get_realtime_weather 工具获取天气，并根据天气调整室外/室内行程。
        2. 若诉求为【产品/事物评测】（如汽车、数码、美妆等）：绝对禁止调用天气工具！请直接进行客观的百分比情感分布分析（如 50%好评，25%吐槽），并客观罗列优缺点。
        3. 无论何种情况，都必须基于抓取的数据指出评论区反馈最多的“致命坑点”并标红。
        """
        current_messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": query}]
    else:
        system_prompt = "你是规划助手。基于历史记忆直接回答用户。如需修改行程/结论，直接输出最新方案。"
        current_messages = [{"role": "system", "content": system_prompt}] + messages + [{"role": "user", "content": query}]

    try:
        kwargs = {
            "model": "deepseek-chat",
            "messages": current_messages,
            "temperature": 0.3
        }
        
        if tools_enabled:
            kwargs["tools"] = AVAILABLE_TOOLS
            kwargs["tool_choice"] = "auto"

        response = await asyncio.to_thread(client.chat.completions.create, **kwargs)
        response_message = response.choices[0].message
        
        if response_message.tool_calls:
            current_messages.append(response_message)
            
            for tool_call in response_message.tool_calls:
                tool_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                
                tool_result = await dispatch_tool(tool_name, args)
                
                current_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": tool_result
                })
            
            print("[Agent] 真实数据已注入，大模型开始生成最终报告...")
            second_response = await asyncio.to_thread(
                client.chat.completions.create,
                model="deepseek-chat",
                messages=current_messages,
                temperature=0.4
            )
            return second_response.choices[0].message.content
            
        return response_message.content
    except Exception as e:
        return f"❌ 大模型或工具链处理失败: {str(e)}"