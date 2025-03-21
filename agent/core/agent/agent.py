import json
import os
from typing import Dict

import dotenv

from agent.config.settings import SYSTEM_PROMPT_WITH_TOOLS
from agent.core.model.llm import LLMClient
from agent.core.tools.get_stock_data import GetStockDataTool
from agent.core.tools.search_stock_news import SearchStockNews
from agent.core.tools.short_term_analysis import ShortTermAnalysis

dotenv.load_dotenv()


class Agent:
    """管理工具集合和LLM交互的类"""

    def __init__(self):
        # 初始化所有工具
        self.tools = {
            "get_stock_data": GetStockDataTool(),
            "search_stock_news": SearchStockNews(),
            "short_term_analysis": ShortTermAnalysis()
            # todo 完成技术分析
            # todo 本周需要完成，1、新闻抓取 2、总结新闻，以及短期
            # todo 获取历史数据，走指定策略的回归
            # todo 本周需要完成可视化
        }

        # 初始化LLM客户端
        # self.llm = LLMClient(base_url=os.getenv("OPENAI_API_BASE"), api_key=os.getenv("OPENAI_API_KEY"))
        self.llm = LLMClient()

        # 转换工具为OpenAI格式
        self.openai_tools = self._convert_tools_to_openai_format()

    def _convert_tools_to_openai_format(self):
        """将工具转换为OpenAI tools格式"""
        openai_tools = []
        for name, tool in self.tools.items():
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            })
        return openai_tools

    def _handle_tool_calls(self, tool_calls):
        """处理工具调用返回结果"""
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            try:
                parameters = json.loads(tool_call.function.arguments)
                result = self.execute_tool(tool_name, **parameters)
                results.append({
                    "tool_call_id": tool_call.id,
                    "output": json.dumps(result, ensure_ascii=False)
                })
            except Exception as e:
                results.append({
                    "tool_call_id": tool_call.id,
                    "output": f"工具执行错误: {str(e)}"
                })
        return results

    def get_tool_descriptions(self) -> str:
        """生成所有工具的描述信息"""
        descriptions = []
        for name, tool in self.tools.items():
            desc = f"Tool: {name}\nDescription: {tool.description}\nParameters: {json.dumps(tool.parameters, indent=2)}\n"
            descriptions.append(desc)
        return "\n".join(descriptions)

    def execute_tool(self, tool_name: str, **params) -> Dict:
        """执行指定的工具"""
        if tool_name not in self.tools:
            return {"error": f"Tool {tool_name} not found"}

        tool = self.tools[tool_name]
        try:
            result = tool.execute(**params)
            return result
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}

    def query_with_tools(self, stock_id: str, query: str) -> str:
        """使用工具和LLM处理查询"""
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT_WITH_TOOLS
            },
            {
                "role": "user",
                "content": f"stock id: {stock_id}\nQuery: {query}"
            }
        ]

        while True:
            response = self.llm.get_response_with_tools(
                # model="gpt-4o-2024-11-20",
                messages=messages,
                tools=self.openai_tools
            )

            print(response)
            if not response:
                return "LLM call failed"

            if response["type"] == "message":
                return response["content"]

            # Handle tool calls
            tool_results = self._handle_tool_calls(response["tool_calls"])
            print(f"Tool results: {tool_results}")

            # Add tool execution results to message history
            messages.append({
                "role": "assistant",
                "tool_calls": response["tool_calls"]
            })
            messages.append({
                "role": "tool",
                "tool_call_id": tool_results[0]["tool_call_id"],
                "content": tool_results[0]["output"]
            })
