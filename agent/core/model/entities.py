from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict
import pandas as pd

@dataclass
class StockData:
    code: str
    name: str
    data: pd.DataFrame
    last_update: datetime

@dataclass
class PredictionResult:
    code: str
    date: datetime
    predicted_price: float
    confidence: float
    signals: List[str]

@dataclass
class TradeSignal:
    code: str
    date: datetime
    action: str  # 'BUY' or 'SELL'
    price: float
    volume: float
    reason: str

@dataclass
class MarketSentiment:
    code: str
    date: datetime
    sentiment_score: float
    hot_degree: float
    news_summary: str
    keywords: List[str]

@dataclass
class AIAnalysisReport:
    code: str
    date: datetime
    analysis: str
    risk_level: str
    opportunities: List[str]
    threats: List[str]
    recommendation: str 

@dataclass
class FinancialReportAnalysis:
    code: str
    date: datetime
    report_url: str
    key_metrics: Dict[str, str]
    growth_analysis: str
    risk_factors: List[str]
    recommendations: str
    summary: str 