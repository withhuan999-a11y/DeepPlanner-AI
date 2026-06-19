import asyncio
from .weather import WEATHER_TOOL_SCHEMA, execute_weather

# 向 Agent 注册所有可用工具
AVAILABLE_TOOLS = [WEATHER_TOOL_SCHEMA]

async def dispatch_tool(tool_name: str, kwargs: dict) -> str:
    """统一的工具派发中心，后续增加新工具在此扩展分支"""
    if tool_name == "get_realtime_weather":
        city_name = kwargs.get("city")
        return await asyncio.to_thread(execute_weather, city_name)
        
    raise ValueError(f"调用了未注册的工具: {tool_name}")