from typing import Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from ..config.settings import Settings
from ..models.entities import StockData


class DataProcessor:
    def __init__(self):
        self.scaler = MinMaxScaler(feature_range=(0, 1))

    def prepare_lstm_data(self, stock_data: StockData,
                         time_step: int = Settings.LSTM.time_step) -> Tuple[np.ndarray, np.ndarray]:
        """准备LSTM模型的训练数据"""
        # 获取收盘价数据
        data = stock_data.data['Close'].values.reshape(-1, 1)
        # 数据归一化
        scaled_data = self.scaler.fit_transform(data)
        # 创建时间序列数据
        X, y = [], []
        for i in range(len(scaled_data) - time_step):
            X.append(scaled_data[i:(i + time_step), 0])
            y.append(scaled_data[i + time_step, 0])
        return np.array(X), np.array(y)
    def prepare_turtle_data(self, stock_data: StockData) -> pd.DataFrame:
        """准备海龟交易策略所需的数据"""
        df = stock_data.data.copy()
        # 计算真实波幅(TR)
        df['TR'] = np.maximum(
            df['High'] - df['Low'],
            np.maximum(
                abs(df['High'] - df['Close'].shift(1)),
                abs(df['Low'] - df['Close'].shift(1))
            )
        )
        # 计算ATR
        df['ATR'] = df['TR'].rolling(window=Settings.TURTLE.atr_window).mean()
        # 计算唐奇安通道
        df['High_20'] = df['High'].rolling(window=Settings.TURTLE.short_window).max()
        df['Low_20'] = df['Low'].rolling(window=Settings.TURTLE.short_window).min()
        df['High_55'] = df['High'].rolling(window=Settings.TURTLE.long_window).max()
        df['Low_55'] = df['Low'].rolling(window=Settings.TURTLE.long_window).min()
        return df
    def inverse_transform_prices(self, scaled_prices: np.ndarray) -> np.ndarray:
        """将归一化的价格数据转换回原始价格"""
        return self.scaler.inverse_transform(scaled_prices.reshape(-1, 1))
    @staticmethod
    def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
        df = df.data.copy()
        """计算技术指标"""
        # 1. 趋势指标
        # 移动平均线
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA10'] = df['Close'].rolling(window=10).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()

        # 指数移动平均线(EMA)
        df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()

        # MACD
        df['MACD'] = df['EMA12'] - df['EMA26']
        df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Histogram'] = df['MACD'] - df['Signal_Line']

        # 2. 动量指标
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # KDJ
        low_min = df['Low'].rolling(window=9).min()
        high_max = df['High'].rolling(window=9).max()
        df['K'] = 100 * ((df['Close'] - low_min) / (high_max - low_min))
        df['D'] = df['K'].rolling(window=3).mean()
        df['J'] = 3 * df['K'] - 2 * df['D']

        # 3. 波动性指标
        # Bollinger Bands
        df['BB_middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
        df['BB_lower'] = df['BB_middle'] - (bb_std * 2)

        # ATR (Average True Range)
        df['TR'] = np.maximum(
            df['High'] - df['Low'],
            np.maximum(
                abs(df['High'] - df['Close'].shift(1)),
                abs(df['Low'] - df['Close'].shift(1))
            )
        )
        df['ATR'] = df['TR'].rolling(window=14).mean()

        # 4. 成交量指标
        # OBV (On Balance Volume)
        df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).cumsum()

        # Volume MA
        df['Volume_MA5'] = df['Volume'].rolling(window=5).mean()
        df['Volume_MA20'] = df['Volume'].rolling(window=20).mean()

        # 5. 趋势强度指标
        # ADX (Average Directional Index)
        plus_dm = df['High'].diff()
        minus_dm = df['Low'].diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm > 0] = 0

        tr = df['TR']
        plus_di = 100 * (plus_dm.rolling(window=14).mean() / tr.rolling(window=14).mean())
        minus_di = 100 * (minus_dm.rolling(window=14).mean() / tr.rolling(window=14).mean())
        df['ADX'] = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)

        # 6. 价格动量指标
        # ROC (Rate of Change)
        df['ROC'] = df['Close'].pct_change(periods=12) * 100

        # Williams %R
        df['Williams_R'] = ((df['High'].rolling(14).max() - df['Close']) /
                            (df['High'].rolling(14).max() - df['Low'].rolling(14).min())) * -100
        return df