import requests
import PyPDF2
import io
import os
import hashlib
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path
from trade.models.entities import FinancialReportAnalysis
from trade.utils.logger import Logger
from trade.config.settings import Settings
import json

class FinancialReportAnalyzer:
    def __init__(self):
        self.logger = Logger()
        self.reports_dir = Path(Settings.DATA.financial_reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
    def analyze(self, stock_code: str, report_source: str) -> Optional[FinancialReportAnalysis]:
        """分析财务报告
        
        Args:
            stock_code: 股票代码
            report_source: 可以是URL或本地文件路径
        """
        try:
            # 获取报告文本
            report_text = self._get_report_text(report_source)
            if not report_text:
                raise ValueError("无法获取财报内容")
                
            # 使用AI模型分析财报
            analysis_result = self._analyze_with_ai(stock_code, report_text)
            
            return FinancialReportAnalysis(
                code=stock_code,
                date=datetime.now(),
                report_url=report_source,
                key_metrics=analysis_result.get('key_metrics', {}),
                growth_analysis=analysis_result.get('growth_analysis', ''),
                risk_factors=analysis_result.get('risk_factors', []),
                recommendations=analysis_result.get('recommendations', ''),
                summary=analysis_result.get('summary', '')
            )
            
        except Exception as e:
            self.logger.error(f"财报分析错误: {str(e)}")
            return None
            
    def _get_report_text(self, source: str) -> Optional[str]:
        """获取报告文本，支持URL和本地文件"""
        try:
            # 判断是URL还是本地文件路径
            if source.startswith(('http://', 'https://')):
                return self._get_report_from_url(source)
            else:
                return self._get_report_from_file(source)
        except Exception as e:
            self.logger.error(f"获取报告文本失败: {str(e)}")
            return None
            
    def _get_report_from_url(self, url: str) -> Optional[str]:
        """从URL获取报告内容"""
        try:
            # 生成文件名
            file_name = self._generate_report_filename(url)
            local_path = self.reports_dir / file_name
            
            # 检查是否已经下载
            if local_path.exists():
                self.logger.info(f"使用本地缓存的报告: {local_path}")
                return self._get_report_from_file(str(local_path))
                
            # 下载PDF
            response = requests.get(url)
            response.raise_for_status()
            
            # 保存文件
            local_path.write_bytes(response.content)
            self.logger.info(f"报告已下载到: {local_path}")
            
            # 解析PDF内容
            return self._parse_pdf(local_path)
            
        except Exception as e:
            self.logger.error(f"从URL获取报告失败: {str(e)}")
            return None
            
    def _get_report_from_file(self, file_path: str) -> Optional[str]:
        """从本地文件获取报告内容"""
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")
                
            return self._parse_pdf(path)
            
        except Exception as e:
            self.logger.error(f"从文件读取报告失败: {str(e)}")
            return None
            
    def _parse_pdf(self, pdf_path: Path) -> Optional[str]:
        """解析PDF文件"""
        try:
            pdf_reader = PyPDF2.PdfReader(str(pdf_path))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
            
        except Exception as e:
            self.logger.error(f"PDF解析失败: {str(e)}")
            return None
            
    def _generate_report_filename(self, url: str) -> str:
        """生成报告文件名"""
        # 使用URL的MD5作为文件名的一部分
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        # 从URL中提取文件名
        original_name = url.split('/')[-1]
        # 如果URL中没有文件名，使用时间戳
        if not original_name or not original_name.endswith('.pdf'):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return f"report_{url_hash}_{timestamp}.pdf"
        return f"{url_hash}_{original_name}"

    def _analyze_with_ai(self, stock_code: str, report_text: str) -> Dict:
        """使用AI模型分析财报内容"""
        try:
            prompt = self._generate_analysis_prompt(stock_code, report_text)
            
            # 调用Ollama API
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": Settings.AI.model_name,
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                return self._parse_ai_response(response.text)
            else:
                raise Exception(f"AI API错误: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"AI分析错误: {str(e)}")
            return {}
            
    def _generate_analysis_prompt(self, stock_code: str, report_text: str) -> str:
        """生成AI分析提示"""
        return f"""你是一个专业的财务分析师AI助手。请分析下面的财报内容，并严格按照指定的JSON格式返回分析结果。
注意：
1. 只返回JSON格式的内容，不要包含任何其他文字说明
2. 不要使用markdown格式或代码块
3. 确保返回的是合法的JSON格式

分析对象: {stock_code}
财报内容:
{report_text[:200000]}...

返回格式:
{{
    "key_metrics": {{
        "revenue": "具体的收入分析，包括同比增长等",
        "profit_margin": "利润率分析，包括毛利率和净利率",
        "cash_flow": "经营性现金流和自由现金流分析",
        "debt_ratio": "资产负债率和偿债能力分析"
    }},
    "growth_analysis": "对公司整体增长情况的详细分析，包括收入增长、利润增长等",
    "risk_factors": [
        "具体的风险因素1",
        "具体的风险因素2",
        "具体的风险因素3"
    ],
    "recommendations": "基于财报分析的具体投资建议",
    "summary": "财报分析的总体结论"
}}"""

    def _parse_ai_response(self, response: str) -> Dict:
        """解析AI响应"""
        try:
            # 尝试直接解析JSON
            all_response = json.loads(response)
            cleaned_response = all_response['response'].replace("```json", "").replace("```", "").strip()
            cleaned_response = cleaned_response[:cleaned_response.rfind('}')+1]
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