from typing import Any, Dict, Optional

import yfinance as yf
import pandas_ta as ta

from agent.core.tools.base import BaseTool


class GetStockDataTool(BaseTool):
    """Tool for performing semantic search over codebase using Repository."""

    @property
    def name(self) -> str:
        return "get_stock_data"

    # def __init__(
    #         self,
    #         stockData: Optional[st] = None,
    # ):
    #     self.repository = Repository(
    #         model=repository.model,
    #         vector_client=repository.vector_client,
    #         rerank_model=repository.rerank_model,
    #     )

    @property
    def description(self) -> str:
        return """Retrieve historical stock data from Yahoo Finance (includes open, close, high, low prices, trading volume, etc.)"""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
                "type": "object",
                "properties": {
                        "stock_id": {
                            "type": "string",
                            "description": "Stock symbol or company name (e.g.: AAPL, TSLA)"
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date for data retrieval (YYYY-MM-DD format, mutually exclusive with period)",
                            "format": "date"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date for data retrieval (YYYY-MM-DD format, mutually exclusive with period)",
                            "format": "date"
                        },
                        "period": {
                            "type": "string",
                            "description": "Data period (default '6mo')",
                            "enum": ["1d","5d","1wk","1mo","3mo","6mo","1y","2y","5y","10y","ytd","max"]
                        },
                        "interval": {
                            "type": "string",
                            "description": "Data interval frequency (e.g. '1d' for daily). Valid values: 1m,2m,5m,15m,30m,60m,90m,1h,1d,1wk,1mo,3mo",
                            "enum": ["1m","2m","5m","15m","30m","60m","90m","1h","1d","1wk","1mo","3mo"]
                        }
                    },
                    "required": ["stock_id", "interval", "period"]
                }

    def calculate_technical_indicators(self, df):
        """计算技术指标"""
        # 移动平均线
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA10'] = df['Close'].rolling(window=10).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()

        # RSI
        df['RSI'] = df.ta.rsi(length=14)

        # MACD
        macd = df.ta.macd(fast=12, slow=26, signal=9)
        df['MACD'] = macd['MACD_12_26_9']
        df['MACD_Signal'] = macd['MACDs_12_26_9']
        df['MACD_Hist'] = macd['MACDh_12_26_9']

        # 布林带
        bollinger = df.ta.bbands(length=20)
        df['BB_Upper'] = bollinger['BBU_20_2.0']
        df['BB_Middle'] = bollinger['BBM_20_2.0']
        df['BB_Lower'] = bollinger['BBL_20_2.0']

        # 成交量指标
        df['Volume_MA5'] = df['Volume'].rolling(window=5).mean()

        # KDJ
        kdj = df.ta.kdj()
        df['KDJ_K'] = kdj['K_9_3']
        df['KDJ_D'] = kdj['D_9_3']
        df['KDJ_J'] = kdj['J_9_3']

        return df

    def execute(
            self,
            stock_id: str,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            period: Optional[str] = None,
            interval: str = "1d"
    ) -> Dict[str, Any]:
        try:
            # 本地模型太拉垮了，先写死，后续再看情况进行优化
            ticker = yf.Ticker(stock_id)
            data = ticker.history(start=start_date, end=end_date,
                                  period="1y", interval="1d")

            # 移除时区信息
            if data.index.tz is not None:
                data.index = data.index.tz_localize(None)

            # 检查数据是否为空
            if data is None or len(data) == 0 or data.shape[0] == 0:
                return {
                    "status": "error",
                    "error": f"未能获取到股票 {stock_id} 的数据或数据为空",
                    "data": None
                }

            # 计算技术指标
            data = self.calculate_technical_indicators(data)

            # 处理数据
            data.reset_index(inplace=True)
            data['Date'] = data['Date'].astype(str)
            # 处理 NaN 值
            data = data.fillna('')
            last_day_data = data.iloc[-1:].to_dict(orient='records')[0]

            return {
                "status": "success",
                "data": last_day_data,
                "error": None
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"获取股票数据失败: {str(e)}",
                "data": None
            }


def main():
    tool = GetStockDataTool()
    # 测试获取苹果股票的数据 513130.SS
    result = tool.execute(stock_id="AAPL", period="1y", interval="1d")

    # 格式化输出结果
    print(result)


if __name__ == '__main__':
    main()
