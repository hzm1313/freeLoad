from typing import List, Dict, Any
import pandas as pd
from pathlib import Path
from datetime import datetime
from ..models.entities import PredictionResult, TradeSignal, MarketSentiment, AIAnalysisReport

class ExcelWriter:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
    
    def _get_output_path(self, prefix: str) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.output_dir / f"{prefix}_{timestamp}.xlsx"
    
    def write_predictions(self, predictions: List[PredictionResult]):
        df = pd.DataFrame([
            {
                "股票代码": p.code,
                "预测日期": p.date,
                "预测价格": p.predicted_price,
                "置信度": p.confidence,
                "信号": ", ".join(p.signals)
            }
            for p in predictions
        ])
        output_path = self._get_output_path("predictions")
        df.to_excel(output_path, index=False)
        return output_path
    
    def write_trade_signals(self, signals: List[TradeSignal]):
        df = pd.DataFrame([
            {
                "股票代码": s.code,
                "交易日期": s.date,
                "交易动作": s.action,
                "交易价格": s.price,
                "交易数量": s.volume,
                "交易原因": s.reason
            }
            for s in signals
        ])
        output_path = self._get_output_path("trade_signals")
        df.to_excel(output_path, index=False)
        return output_path
    
    def write_sentiment_analysis(self, sentiments: List[MarketSentiment]):
        df = pd.DataFrame([
            {
                "股票代码": s.code,
                "分析日期": s.date,
                "情绪得分": s.sentiment_score,
                "热度": s.hot_degree,
                "新闻摘要": s.news_summary,
                "关键词": ", ".join(s.keywords)
            }
            for s in sentiments
        ])
        output_path = self._get_output_path("sentiment_analysis")
        df.to_excel(output_path, index=False)
        return output_path
    
    def write_ai_reports(self, reports: List[AIAnalysisReport]):
        df = pd.DataFrame([
            {
                "股票代码": r.code,
                "分析日期": r.date,
                "分析报告": r.analysis,
                "风险等级": r.risk_level,
                "机会": ", ".join(r.opportunities),
                "威胁": ", ".join(r.threats),
                "建议": r.recommendation
            }
            for r in reports
        ])
        output_path = self._get_output_path("ai_reports")
        df.to_excel(output_path, index=False)
        return output_path 