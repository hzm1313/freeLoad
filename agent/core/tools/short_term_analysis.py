from datetime import datetime
from typing import Any, Dict

from agent.core.model.llm import LLMClient
from agent.core.tools.base import BaseTool
from agent.core.tools.get_stock_data import GetStockDataTool
from agent.core.tools.search_stock_news import SearchStockNews


class ShortTermAnalysis(BaseTool):
    def __init__(self):
        self.llm_client = LLMClient()

    @property
    def name(self) -> str:
        return "short_term_analysis"

    @property
    def description(self) -> str:
        return """基于股市信息以及新闻来进行短线预测"""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "stock_id": {
                    "type": "string",
                    "description": "股票代码"
                },
                "stock_data": {
                    "type": "object",
                    "description": "股票数据"
                },
                "news_data": {
                    "type": "object",
                    "description": "新闻数据"
                }
            },
            "required": ["stock_data", "news_data"]
        }

    def execute(self, stock_id: str, stock_data: Dict[str, Any], news_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # 验证输入数据
            if stock_data["status"] != "success":
                return {
                    "status": "error",
                    "error": f"股票数据无效: {stock_data.get('error', '未知错误')}",
                    "data": None
                }

            if news_data["status"] != "success":
                return {
                    "status": "error",
                    "error": f"新闻数据无效: {news_data.get('error', '未知错误')}",
                    "data": None
                }

            # 构建 LLM 提示词
            messages = [
                {"role": "system", "content": """你是一个专业的股票分析师，请基于提供的股票数据和新闻信息，
                进行短期走势分析。请从以下几个方面进行分析：
                1. 技术面分析：基于价格趋势、成交量等
                2. 消息面分析：基于最新新闻对股价的潜在影响
                3. 短期风险提示
                4. 未来3-5个交易日的走势预判
                请确保分析专业、客观，并给出明确的观点。"""},
                {"role": "user", "content": f"""
                股票代码：{stock_id}
                基本面信息：
                {stock_data['basic_info']}
                
                最近交易数据：
                {stock_data['history_data'][-5:]}  # 最近5天数据
                相关新闻：
                {news_data['news']}
                请进行分析。
                """}
            ]

            print("=========start===========")
            print(messages)
            print("=========end===========")

            # 调用 LLM 获取分析结果
            analysis_result = self.llm_client.get_response(
                messages=messages,
                temperature=0.7
            )

            return {
                "status": "success",
                "stock_id": stock_id,
                "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data": {
                    "stock_info": stock_data["basic_info"],
                    "recent_data": stock_data["history_data"][-5:],
                    "recent_news": news_data["news"],
                    "analysis": analysis_result
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"分析过程发生错误: {str(e)}",
                "data": None
            }


def main():
    # 示例：先获取数据，再进行分析
    stock_tool = GetStockDataTool()
    news_tool = SearchStockNews()

    # 获取股票数据
    stock_data = stock_tool.execute(
        stock_id="AAPL",
        period="30d",
        interval="1d"
    )

    # 获取新闻数据
    news_data = news_tool.execute(
        stock_id="AAPL",
        limit=5
    )

    # 进行分析
    tool = ShortTermAnalysis()
    result = tool.execute(
        stock_id="AAPL",
        stock_data=stock_data,
        news_data=news_data
    )

    if result["status"] == "success":
        print(f"\n=== {result['stock_id']} 短线分析 ===")
        print(f"分析时间: {result['analysis_time']}\n")
        print("=== 分析结果 ===")
        print(result["data"]["analysis"])
        print("-" * 50)
    else:
        print(f"错误: {result['error']}")


if __name__ == '__main__':
    main()
