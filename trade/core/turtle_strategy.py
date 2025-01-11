import pandas as pd
import numpy as np
from typing import List, Optional
from datetime import datetime

from ..models.entities import StockData, TradeSignal
from ..utils.data_processor import DataProcessor
from ..utils.logger import Logger
from ..config.settings import Settings

class TurtleStrategy:
    def __init__(self):
        self.logger = Logger()
        self.data_processor = DataProcessor()
        self.config = Settings.TURTLE
        
    def analyze(self, stock_data: StockData) -> List[TradeSignal]:
        """分析股票数据并生成交易信号"""
        try:
            # 准备数据
            df = self.data_processor.prepare_turtle_data(stock_data)
            
            # 生成交易信号
            signals = []
            
            for i in range(1, len(df)):
                current_row = df.iloc[i]
                prev_row = df.iloc[i-1]
                
                # 计算突破信号
                entry_signal = self._check_entry_signal(current_row, prev_row)
                exit_signal = self._check_exit_signal(current_row, prev_row)
                
                if entry_signal or exit_signal:
                    signal = self._create_trade_signal(
                        stock_data.code,
                        df.index[i],
                        current_row,
                        "BUY" if entry_signal else "SELL"
                    )
                    signals.append(signal)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Error analyzing with turtle strategy: {str(e)}")
            raise
    
    def _check_entry_signal(self, current: pd.Series, prev: pd.Series) -> bool:
        """检查入场信号"""
        # 价格突破20日高点
        if current['Close'] > prev['High_20']:
            return True
        return False
    
    def _check_exit_signal(self, current: pd.Series, prev: pd.Series) -> bool:
        """检查出场信号"""
        # 价格跌破20日低点
        if current['Close'] < prev['Low_20']:
            return True
        return False
    
    def _create_trade_signal(self, code: str, date: datetime, 
                           row: pd.Series, action: str) -> TradeSignal:
        """创建交易信号"""
        # 计算交易单位
        unit_size = self._calculate_position_size(row['ATR'])
        
        return TradeSignal(
            code=code,
            date=date.date(),
            action=action,
            price=row['Close'],
            volume=unit_size,
            reason=self._generate_signal_reason(action, row)
        )
    
    def _calculate_position_size(self, atr: float) -> float:
        """计算仓位大小"""
        dollar_volatility = atr
        position_size = (self.config.total_risk_capital * 
                        self.config.risk_percentage) / dollar_volatility
        return position_size
    
    def _generate_signal_reason(self, action: str, row: pd.Series) -> str:
        """生成交易信号原因"""
        if action == "BUY":
            return (f"价格突破20日高点 {row['High_20']:.2f}, "
                   f"ATR为 {row['ATR']:.2f}")
        else:
            return (f"价格跌破20日低点 {row['Low_20']:.2f}, "
                   f"ATR为 {row['ATR']:.2f}") 