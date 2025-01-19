import pandas as pd
import numpy as np
from typing import List, Optional
from datetime import datetime

from ..models.entities import StockData, TradeSignal
from ..utils.data_processor import DataProcessor
from ..utils.logger import Logger
from ..config.settings import Settings

class TurtleStrategy:
    """
    海龟交易策略实现类
    基于经典的海龟交易法则，包含突破入场、止损和仓位管理等核心功能
    """
    def __init__(self):
        """
        初始化海龟策略所需的组件
        - logger: 日志记录器
        - data_processor: 数据处理器
        - config: 海龟策略配置参数
        """
        self.logger = Logger()
        self.data_processor = DataProcessor()
        self.config = Settings.TURTLE
        
    def analyze(self, stock_data: StockData) -> List[TradeSignal]:
        """
        分析股票数据并生成交易信号
        
        Args:
            stock_data: 包含OHLCV数据的股票数据对象
            
        Returns:
            List[TradeSignal]: 交易信号列表
            
        Raises:
            Exception: 当分析过程出现错误时抛出异常
        """
        try:
            # 使用数据处理器准备海龟策略所需的技术指标数据
            df = self.data_processor.prepare_turtle_data(stock_data)
            
            # 存储生成的交易信号
            signals = []
            
            # 遍历每个交易日，检查交易信号
            for i in range(1, len(df)):
                current_row = df.iloc[i]
                prev_row = df.iloc[i-1]
                
                # 分别检查入场和出场信号
                entry_signal = self._check_entry_signal(current_row, prev_row)
                exit_signal = self._check_exit_signal(current_row, prev_row)
                
                # 如果存在任何信号，创建交易信号对象
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
            self.logger.error(f"海龟策略分析过程出错: {str(e)}")
            raise
    
    def _check_entry_signal(self, current: pd.Series, prev: pd.Series) -> bool:
        """
        检查入场信号
        
        Args:
            current: 当前交易日的数据
            prev: 前一个交易日的数据
            
        Returns:
            bool: 如果出现入场信号返回True，否则返回False
        """
        # 当收盘价突破20日高点时，产生做多信号
        if current['Close'] > prev['High_20']:
            return True
        return False
    
    def _check_exit_signal(self, current: pd.Series, prev: pd.Series) -> bool:
        """
        检查出场信号
        
        Args:
            current: 当前交易日的数据
            prev: 前一个交易日的数据
            
        Returns:
            bool: 如果出现出场信号返回True，否则返回False
        """
        # 当收盘价跌破20日低点时，产生平仓信号
        if current['Close'] < prev['Low_20']:
            return True
        return False
    
    def _create_trade_signal(self, code: str, date: datetime, 
                           row: pd.Series, action: str) -> TradeSignal:
        """
        创建交易信号对象
        
        Args:
            code: 股票代码
            date: 交易日期
            row: 当前交易日的数据
            action: 交易动作（'BUY'或'SELL'）
            
        Returns:
            TradeSignal: 包含完整交易信息的信号对象
        """
        # 基于ATR计算合适的仓位大小
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
        """
        计算交易仓位大小
        
        Args:
            atr: 平均真实波幅值
            
        Returns:
            float: 建议的仓位大小
            
        说明:
            基于账户风险和ATR计算适当的仓位大小，
            确保单次交易的风险不超过账户总值的固定比例
        """
        dollar_volatility = atr
        position_size = (self.config.total_risk_capital * 
                        self.config.risk_percentage) / dollar_volatility
        return position_size
    
    def _generate_signal_reason(self, action: str, row: pd.Series) -> str:
        """
        生成交易信号的具体原因描述
        
        Args:
            action: 交易动作
            row: 当前交易日的数据
            
        Returns:
            str: 描述交易信号产生原因的字符串
        """
        if action == "BUY":
            return (f"价格突破20日高点 {row['High_20']:.2f}, "
                   f"ATR为 {row['ATR']:.2f}")
        else:
            return (f"价格跌破20日低点 {row['Low_20']:.2f}, "
                   f"ATR为 {row['ATR']:.2f}") 