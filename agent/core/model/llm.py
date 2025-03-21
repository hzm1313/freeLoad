import json
import os

import dotenv
from openai import OpenAI

dotenv.load_dotenv()

class LLMClient:
    def __init__(
            self,
            base_url="http://localhost:11434/v1",
            api_key="ollama",
            # default_model="PetrosStav/gemma3-tools:12b",
            default_model="qwen2.5:7b-instruct-q6_K",
            # default_model="mistral:latest",
    ):
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.default_model = default_model

    def get_response(self, messages, model=None, temperature=0.1, stream=False):
        try:
            model = model or self.default_model
            response = self.client.chat.completions.create(
                model=model, temperature=temperature, messages=messages, stream=stream
            )

            if not stream:
                return response.choices[0].message.content
            else:
                return self._stream_response(response)
        except Exception as e:
            print(f"Error in LLMClient: {str(e)}")
            return None

    def _stream_response(self, response):
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    def get_response_with_tools(self, messages, tools, model=None, temperature=0):
        try:
            model = model or self.default_model
            response = self.client.chat.completions.create(
                model=model,
                temperature=temperature,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                stream=False
            )

            message = response.choices[0].message

            # 如果返回tool_calls,需要执行工具调用
            if message.tool_calls:
                return {
                    "type": "tool_calls",
                    "tool_calls": message.tool_calls
                }

            # 否则返回普通文本响应
            return {
                "type": "message",
                "content": message.content
            }

        except Exception as e:
            print(f"Error in LLMClient tool call: {str(e)}")
            print(json.dumps(messages, indent=2))
            return None


if __name__ == "__main__":
    # ollama 无需配置
    # local_client = LLMClient(base_url=os.getenv("OPENAI_API_BASE"), api_key=os.getenv("OPENAI_API_KEY"))
    local_client = LLMClient()

    print("尝试连接到 Ollama 服务...")

    # 测试连接
    test_response = local_client.client.models.list()
    print(f"连接成功! 可用模型: {[model.id for model in test_response.data]}")

    # 测试流式 tools 响应
    print("\n=== Testing streaming response ===")
    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_weather",
                "description": "获取指定城市的天气信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "城市名称"
                        },
                        "date": {
                            "type": "string",
                            "description": "日期，格式 YYYY-MM-DD，可选",
                        }
                    },
                    "required": ["city"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "calculate",
                "description": "执行基础数学计算",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "数学表达式，如 1 + 2 * 3"
                        }
                    },
                    "required": ["expression"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_database",
                "description": "在数据库中搜索信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索关键词"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "返回结果数量限制",
                            "default": 10
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]

    # 使用示例
    messages = [{"role": "user", "content": "北京今天天气怎么样？"}]
    print(local_client.get_response_with_tools(model="llama3-groq-tool-use:latest", messages=messages, tools=tools))

    # 测试普通响应
    print("\n=== Testing normal response ===")
    print(
        local_client.get_response(messages=[{"role": "user", "content": "你是谁？"}],
                                  stream=False)
    )

    # 测试指定其他模型
    print("\n=== Testing normal change mode response ===")
    print(
        local_client.get_response(model="gemma2:2b", messages=[{"role": "user", "content": "你是谁？"}],
                                  stream=False)
    )

    # 测试流式响应
    print("\n=== Testing streaming response ===")
    stream = local_client.get_response(messages=[{"role": "user", "content": "你是谁？"}],
                                       stream=True)

    if stream:
        for chunk in stream:
            print(chunk, end='', flush=True)
    print("\n")
