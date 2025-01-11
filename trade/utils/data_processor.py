import pandas as pd
import numpy as np
from typing import Tuple, List
from sklearn.preprocessing import MinMaxScaler
from ..models.entities import StockData
from ..config.settings import Settings

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
        """计算技术指标"""
        # 移动平均线
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA10'] = df['Close'].rolling(window=10).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        return df 