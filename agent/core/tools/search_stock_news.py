from datetime import datetime
from typing import Any, Dict

import yfinance as yf

from agent.core.tools.base import BaseTool


class SearchStockNews(BaseTool):
    """Tool for performing semantic search over codebase using Repository."""

    @property
    def name(self) -> str:
        return "search_stock_news"

    @property
    def description(self) -> str:
        return """搜索股票相关新闻"""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "stock_id": {
                    "type": "string",
                    "description": "股票代码"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回新闻数量限制",
                    "default": 10
                }
            },
            "required": ["stock_id"]
        }

    def execute(self, stock_id: str, limit: int = 10) -> Dict[str, Any]:
        try:
            ticker = yf.Ticker(stock_id)
            news = ticker.news

            if not news:
                return {
                    "status": "error",
                    "error": f"未找到股票 {stock_id} 的相关新闻",
                    "data": None
                }

            # 处理新闻数据
            processed_news = []
            for item in news[:limit]:
                # 转换时间戳为可读格式
                publish_time = datetime.fromtimestamp(item.get('providerPublishTime', 0))

                news_item = {
                    "title": item.get('title', ''),
                    "publisher": item.get('publisher', ''),
                    "link": item.get('link', ''),
                    "publish_time": publish_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "type": item.get('type', ''),
                    "related_tickers": item.get('relatedTickers', []),
                    "summary": item.get('summary', '')
                }
                processed_news.append(news_item)

            return {
                "status": "success",
                "stock_id": stock_id,
                "news_count": len(processed_news),
                "news": processed_news
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"获取股票新闻失败: {str(e)}",
                "data": None
            }


def main():
    tool = SearchStockNews()
    # 测试获取苹果公司的新闻
    result = tool.execute(stock_id="AAPL", limit=5)

    if result["status"] == "success":
        print(f"\n=== {result['stock_id']} 新闻 ===")
        print(f"找到 {result['news_count']} 条新闻\n")

        for idx, news in enumerate(result["news"], 1):
            print(f"新闻 {idx}:")
            print(f"标题: {news['title']}")
            print(f"发布者: {news['publisher']}")
            print(f"发布时间: {news['publish_time']}")
            print(f"链接: {news['link']}")
            print(f"摘要: {news['summary']}")
            print("-" * 50)
    else:
        print(f"错误: {result['error']}")


if __name__ == '__main__':
    main()
