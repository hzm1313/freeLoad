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
    total_risk_capital: float = 100000
    risk_percentage: float = 0.02
    short_window: int = 20
    long_window: int = 55
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