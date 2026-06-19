import json
from uapi import UapiClient
from uapi.errors import UapiError

# 暴露给大模型的接口定义 (Schema)
WEATHER_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_realtime_weather",
        "description": "获取指定城市的实时天气数据。⚠️警告：仅在用户明确进行【旅行/路线规划】且提供具体城市时调用。如果是查询产品、汽车、数码评测等无关天气的请求，绝对禁止调用此工具！",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "需要查询的城市名称，例如：北京、成都"
                }
            },
            "required": ["city"]
        }
    }
}

def execute_weather(city: str) -> str:
    """物理执行天气查询"""
    print(f"[Tool Calling] 大模型请求查询天气: {city}")
    try:
        uapi_client = UapiClient("https://uapis.cn")
        result = uapi_client.misc.get_misc_weather(
            city=city, adcode="", extended=False, 
            forecast=False, hourly=False, minutely=False, 
            indices=False, lang="zh"
        )
        return json.dumps(result, ensure_ascii=False)
    except UapiError as exc:
        print(f"[Tool Calling 失败] API error: {exc}")
        return json.dumps({"error": f"无法获取该城市天气: {exc}"}, ensure_ascii=False)
    except Exception as e:
        print(f"[Tool Calling 失败] {e}")
        return json.dumps({"error": "内部系统错误，未能获取天气。"}, ensure_ascii=False)