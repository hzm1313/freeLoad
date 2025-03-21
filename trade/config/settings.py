from dataclasses import dataclass
from typing import Dict, Any
import os

@dataclass
class ProxyConfig:
    enabled: bool = True
    http: str = "http://11.39.221.0:9091"
    https: str = "http://11.39.221.0:9091"

@dataclass
class DataConfig:
    base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir: str = os.path.join(base_dir, "data")
    output_dir: str = os.path.join(base_dir, "output")
    stock_list_file: str = os.path.join(base_dir, "config", "stock_list.txt")
    financial_reports_dir: str = os.path.join(data_dir, "financial_reports")

@dataclass
class LSTMConfig:
    time_step: int = 10
    epochs: int = 50
    batch_size: int = 32
    validation_split: float = 0.2
    lstm_units: int = 100
    dense_units: int = 50

@dataclass
class TurtleConfig:
    """海龟交易策略配置类
    
    包含海龟交易系统所需的各项关键参数，用于控制资金管理、入场/出场信号和风险控制。
    """
    
    # 总风险资金：用于计算每次交易的资金规模
    # 建议设置为实际可用资金的80%-90%，为意外情况预留缓冲
    total_risk_capital: float = 100000
    
    # 单次交易风险比例：每次交易允许承担的最大损失占总资金的比例
    # 一般建议在1%-2%之间，过高的风险比例可能导致资金大幅回撤
    risk_percentage: float = 0.02
    
    # 短期突破周期：用于生成入场信号的价格突破周期
    # 传统海龟交易法则使用20天，可根据市场特点适当调整
    short_window: int = 20
    
    # 长期突破周期：用于生成更可靠的趋势确认信号
    # 一般设置为短期周期的2-3倍，帮助过滤虚假突破
    long_window: int = 55
    
    # ATR周期：计算真实波幅范围的周期数
    # 用于确定止损位置和仓位规模，一般与短期突破周期保持一致
    atr_window: int = 20

@dataclass
class AIConfig:
    model_type: str = "ollama"  # or "transformers"
    model_name: str = "gemma2:2b"
    api_key: str = ""
    max_tokens: int = 1000

class Settings:
    PROXY = ProxyConfig()
    DATA = DataConfig()
    LSTM = LSTMConfig()
    TURTLE = TurtleConfig()
    AI = AIConfig()

    @classmethod
    def init_directories(cls):
        """初始化必要的目录"""
        os.makedirs(cls.DATA.data_dir, exist_ok=True)
        os.makedirs(cls.DATA.output_dir, exist_ok=True) 