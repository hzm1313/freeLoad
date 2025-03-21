from typing import List, Dict, Optional
import requests
from datetime import datetime
import json

from ..models.entities import StockData, AIAnalysisReport
from ..utils.logger import Logger
from ..config.settings import Settings
from ..utils.data_processor import DataProcessor

class AIAnalyzer:
    def __init__(self):
        self.logger = Logger()
        self.data_processor = DataProcessor()
        self.config = Settings.AI
        
    def analyze(self, stock_data: StockData) -> AIAnalysisReport:
        """使用AI模型分析股票"""
        try:
            # 准备分析数据
            analysis_data = self._prepare_analysis_data(stock_data)
            print(analysis_data)

            # 根据配置选择AI模型
            if self.config.model_type == "ollama":
                analysis_result = self._analyze_with_ollama(analysis_data)
            else:
                analysis_result = self._analyze_with_transformers(analysis_data)
            
            return self._create_report(stock_data.code, analysis_result)
            
        except Exception as e:
            self.logger.error(f"Error in AI analysis: {str(e)}")
            raise
    
    def _prepare_analysis_data(self, stock_data: StockData) -> Dict:
        """准备用于AI分析的数据"""
        df = stock_data.data.copy()
        
        # 计算技术指标
        df = self.data_processor.calculate_technical_indicators(df)
        
        # 提取最近的数据
        recent_data = df.tail(30)  # 最近30天数据
        
        return {
            "code": stock_data.code,
            "current_price": float(df['Close'].iloc[-1]),
            "price_change": float(df['Close'].pct_change().iloc[-1]),
            "volume": float(df['Volume'].iloc[-1]),
            "ma5": float(df['MA5'].iloc[-1]),
            "ma20": float(df['MA20'].iloc[-1]),
            "rsi": float(df['RSI'].iloc[-1]),
            "macd": float(df['MACD'].iloc[-1])
        }
    
    def _analyze_with_ollama(self, data: Dict) -> Dict:
        """使用Ollama模型进行分析"""
        prompt = self._generate_analysis_prompt(data)
        print("[请求模型的 prompt]", prompt)
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.config.model_name,
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                # responseJson = json.loads(response.text)
                # result = responseJson.response
                return self._parse_ai_response(response.text)
            else:
                raise Exception(f"Ollama API error: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Error calling Ollama API: {str(e)}")
            raise
    
    def _analyze_with_transformers(self, data: Dict) -> Dict:
        """使用Transformers模型进行分析"""
        # 实现Transformers模型的调用
        # 这里需要根据实际使用的模型来实现
        pass
    
    def _generate_analysis_prompt(self, data: Dict) -> str:
        """生成AI分析提示"""
        return f"""你是一个专业的股票分析AI助手。请分析以下数据并仅返回JSON格式的分析结果。不要返回任何其他文本。

输入数据:
{{
    "code": "{data['code']}",
    "current_price": {data['current_price']},
    "price_change": {data['price_change']*100:.2f},
    "volume": {data['volume']},
    "ma5": {data['ma5']},
    "ma20": {data['ma20']},
    "rsi": {data['rsi']},
    "macd": {data['macd']}
}}

请严格按照以下JSON格式返回分析结果：
{{
    "analysis": "详细的技术分析内容，包括技术面分析和趋势判断",
    "risk_level": "只能是以下选项之一：低/中/高",
    "opportunities": [
        "投资机会点1",
        "投资机会点2"
    ],
    "threats": [
        "风险因素1",
        "风险因素2"
    ],
    "recommendation": "具体的建议操作"
}}"""
    
    def _parse_ai_response(self, response: str) -> Dict:
        """解析AI响应"""
        try:
            # 尝试直接解析JSON
            all_response = json.loads(response)
            cleaned_response = all_response['response'].replace("```json", "").replace("```", "").strip()
            test = json.loads(cleaned_response)
            return test
        except Exception as e:
            # 如果失败，进行简单的响应处理
            return {
                "analysis": response[:1000],  # 限制长度
                "risk_level": "中",  # 默认风险等级
                "opportunities": ["需要进一步分析"],
                "threats": ["数据解析失败"],
                "recommendation": "建议人工复核"
            }
    
    def _create_report(self, stock_code: str, analysis_result: Dict) -> AIAnalysisReport:
        """创建分析报告"""
        return AIAnalysisReport(
            code=stock_code,
            date=datetime.now(),
            analysis=analysis_result['analysis'],
            risk_level=analysis_result['risk_level'],
            opportunities=analysis_result['opportunities'],
            threats=analysis_result['threats'],
            recommendation=analysis_result['recommendation']
        )


# 你对一个短线交易的专家，尤其擅长波动操作，现在需要你进行明天的股价变化
# 你是一个擅长金融新闻分析和热点分析的专家，我给你提供你最新的公司新闻和股吧讨论信息，需要你预测明天的股票涨跌
# 你是一个六爻的专家，我提供你时间，股票代码，股票名称，预测明天股票的涨跌