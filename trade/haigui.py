import os
from dataclasses import dataclass
from typing import Optional
import pandas as pd
import numpy as np

@dataclass
class TradingConfig:
    """交易配置类"""
    total_risk_capital: float = 100000  # 总资本
    risk_percentage: float = 0.02       # 每笔交易风险
    short_window: int = 20              # 短期窗口
    long_window: int = 55               # 长期窗口
    atr_window: int = 20                # ATR窗口

class TurtleStrategy:
    """海龟交易策略类"""
    
    def __init__(self, config: TradingConfig):
        self.config = config
        self.position: float = 0
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        # 计算ATR
        data['TR'] = np.maximum(
            data['High'] - data['Low'],
            np.abs(data['High'] - data['Close'].shift(1)),
            np.abs(data['Low'] - data['Close'].shift(1))
        )
        data['ATR'] = data['TR'].rolling(window=self.config.atr_window).mean()
        
        # 计算交易单位
        data['Unit'] = (self.config.total_risk_capital * self.config.risk_percentage) / data['ATR']
        
        # 计算突破指标
        data['Short_High'] = data['High'].rolling(window=self.config.short_window).max()
        data['Short_Low'] = data['Low'].rolling(window=self.config.short_window).min()
        data['Long_High'] = data['High'].rolling(window=self.config.long_window).max()
        data['Long_Low'] = data['Low'].rolling(window=self.config.long_window).min()
        
        # 计算信号
        data['Buy_Signal'] = data['Close'] > data['Short_High'].shift(1)
        data['Sell_Signal'] = data['Close'] < data['Short_Low'].shift(1)
        
        return data

    def execute_trades(self, data: pd.DataFrame, stock_name: str) -> None:
        """执行交易策略"""
        self.position = 0
        
        for i in range(1, len(data)):
            if data.loc[i, 'Buy_Signal'] and self.position <= 0:
                self.position = data.loc[i, 'Unit']
                print(f"股票:{stock_name} 日期: {data.loc[i, 'Date']}, 操作: 买入, "
                      f"仓位: {self.position:.2f}, 买入新的头寸")
                
            elif data.loc[i, 'Sell_Signal'] and self.position >= 0:
                self.position = -data.loc[i, 'Unit']
                print(f"股票:{stock_name} 日期: {data.loc[i, 'Date']}, 操作: 卖出, "
                      f"仓位: {self.position:.2f}, 卖出之前的头寸")

class DataProcessor:
    """数据处理类"""
    
    @staticmethod
    def load_stock_data(file_path: str) -> Optional[pd.DataFrame]:
        """加载股票数据"""
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            print(f"加载数据失败: {file_path}, 错误: {str(e)}")
            return None

def main():
    # 获取数据目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_folder_path = os.path.join(current_dir, 'data')
    
    # 初始化策略
    config = TradingConfig()
    strategy = TurtleStrategy(config)
    processor = DataProcessor()
    
    # 处理每个股票文件
    for file in os.listdir(data_folder_path):
        if not file.endswith('.csv'):
            continue
            
        data_file_path = os.path.join(data_folder_path, file)
        data = processor.load_stock_data(data_file_path)
        
        if data is None:
            continue
            
        # 计算指标并执行交易
        data = strategy.calculate_indicators(data)
        strategy.execute_trades(data, file)
        
        # 输出最近20天的预测结果
        print(f"\n{file} 最近20天的预测结果:")
        print(data[['Date', 'Close', 'Buy_Signal', 'Sell_Signal']].tail(20))
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()