from pathlib import Path
from typing import List

import click
import os

from trade.config.settings import Settings
from trade.core.ai_analyzer import AIAnalyzer
from trade.core.data_fetcher import DataFetcher
from trade.core.financial_report_analyzer import FinancialReportAnalyzer
from trade.core.lstm_predictor import LSTMPredictor
from trade.core.sentiment_analyzer import SentimentAnalyzer
from trade.core.turtle_strategy import TurtleStrategy
from trade.models.entities import FinancialReportAnalysis
from trade.utils.excel_writer import ExcelWriter
from trade.utils.logger import Logger


class CLI:
    def __init__(self):
        # 初始化日志记录器
        self.logger = Logger()
        # 初始化数据获取器
        self.data_fetcher = DataFetcher()
        # 初始化LSTM预测器
        self.lstm_predictor = LSTMPredictor()
        # 初始化海龟策略分析器
        self.turtle_strategy = TurtleStrategy()
        # 初始化情绪分析器
        self.sentiment_analyzer = SentimentAnalyzer()
        # 初始化AI分析器
        self.ai_analyzer = AIAnalyzer()
        # 初始化Excel写入器，用于将分析结果写入Excel文件
        self.excel_writer = ExcelWriter(Path(Settings.DATA.output_dir))
        self.financial_report_analyzer = FinancialReportAnalyzer()

    @click.group()
    def cli(self):
        """股票分析和预测工具"""
        pass

    @cli.command()
    @click.argument('stock_codes', nargs=-1)
    @click.option('--period', default='3mo', help='数据周期: 1d/5d/1mo/3mo/6mo/1y/2y/5y/10y/ytd/max')
    @click.option('--interval', default='1d', help='数据间隔: 1m/2m/5m/15m/30m/60m/90m/1h/1d/5d/1wk/1mo/3mo')
    def fetch(self, stock_codes: List[str], period: str = '3mo', interval: str = '1d'):
        """获取股票数据"""
        try:
            # 调用数据获取器获取多只股票的数据
            results = self.data_fetcher.fetch_multiple_stocks(
                stock_codes, period=period, interval=interval
            )
            # 记录成功获取数据的日志
            self.logger.info(f"成功获取 {len(results)} 只股票的数据")
            return results
        except Exception as e:
            # 记录获取数据失败的日志
            self.logger.error(f"获取数据失败: {str(e)}")
            return []

    @cli.command()
    @click.argument('stock_code')
    @click.option('--days', default=5, help='预测天数')
    def predict(self, stock_code: str, days: int):
        """使用LSTM模型预测股票"""
        try:
            # 获取股票数据
            stock_data = self.data_fetcher.fetch_stock_data(stock_code)
            
            # 训练模型并预测
            self.lstm_predictor.train(stock_data)
            predictions = self.lstm_predictor.predict(stock_data, days)
            
            # 输出到Excel
            output_path = self.excel_writer.write_predictions(predictions)
            # 记录预测结果的日志
            self.logger.info(f"预测结果已保存到: {output_path}")
            
        except Exception as e:
            # 记录预测失败的日志
            self.logger.error(f"预测失败: {str(e)}")

    @cli.command()
    @click.argument('stock_code')
    def analyze_turtle(self, stock_code: str):
        """使用海龟策略分析股票"""
        try:
            stock_data = self.data_fetcher.fetch_stock_data(stock_code)
            signals = self.turtle_strategy.analyze(stock_data)
            
            output_path = self.excel_writer.write_trade_signals(signals)
            # 记录海龟策略分析结果的日志
            self.logger.info(f"海龟策略分析结果已保存到: {output_path}")
            
        except Exception as e:
            # 记录海龟策略分析失败的日志
            self.logger.error(f"海龟策略分析失败: {str(e)}")

    @cli.command()
    @click.argument('stock_code')
    def analyze_sentiment(self, stock_code: str):
        """分析市场情绪"""
        try:
            stock_data = self.data_fetcher.fetch_stock_data(stock_code)
            sentiment = self.sentiment_analyzer.analyze(stock_data)
            
            output_path = self.excel_writer.write_sentiment_analysis([sentiment])
            # 记录情绪分析结果的日志
            self.logger.info(f"情绪分析结果已保存到: {output_path}")
            
        except Exception as e:
            # 记录情绪分析失败的日志
            self.logger.error(f"情绪分析失败: {str(e)}")

    @cli.command()
    @click.argument('stock_code')
    @click.option('--model-type', default='ollama', help='AI模型类型: ollama/transformers')
    def analyze_ai(self, stock_code: str, model_type: str):
        """使用AI模型分析股票"""
        try:
            Settings.AI.model_type = model_type
            stock_data = self.data_fetcher.fetch_stock_data(stock_code)
            report = self.ai_analyzer.analyze(stock_data)
            
            output_path = self.excel_writer.write_ai_reports([report])
            # 记录AI分析报告的日志
            self.logger.info(f"AI分析报告已保存到: {output_path}")
            
        except Exception as e:
            # 记录AI分析失败的日志
            self.logger.error(f"AI分析失败: {str(e)}")

    @cli.command()
    @click.argument('stock_code')
    def full_analysis(self, stock_code: str):
        """执行全面分析"""
        try:
            # 获取股票数据
            stock_data = self.data_fetcher.fetch_stock_data(stock_code)
            
            # LSTM预测
            self.lstm_predictor.train(stock_data)
            predictions = self.lstm_predictor.predict(stock_data)
            
            # 海龟策略分析
            signals = self.turtle_strategy.analyze(stock_data)
            
            # 情绪分析
            sentiment = self.sentiment_analyzer.analyze(stock_data)
            
            # AI分析
            report = self.ai_analyzer.analyze(stock_data)
            
            # 保存所有结果
            pred_path = self.excel_writer.write_predictions(predictions)
            signal_path = self.excel_writer.write_trade_signals(signals)
            sentiment_path = self.excel_writer.write_sentiment_analysis([sentiment])
            report_path = self.excel_writer.write_ai_reports([report])
            
            # 记录分析完成的日志
            self.logger.info(f"""
            分析完成，结果保存在以下文件：
            - 预测结果：{pred_path}
            - 交易信号：{signal_path}
            - 情绪分析：{sentiment_path}
            - AI分析报告：{report_path}
            """)
            
        except Exception as e:
            # 记录全面分析失败的日志
            self.logger.error(f"全面分析失败: {str(e)}") 

    @cli.command()
    @click.argument('stock_code')
    @click.argument('report_source')
    @click.option('--is-url', is_flag=True, default=True, help='报告来源是否为URL')
    def analyze_financial_report(self, stock_code: str, report_source: str, is_url: bool):
        """分析财务报告
        
        Args:
            stock_code: 股票代码
            report_source: 财报URL或本地文件路径
            is_url: 是否为URL源
        """
        try:
            click.echo(f"\n📊 开始分析 {stock_code} 的财务报告...")
            
            if not is_url and not os.path.exists(report_source):
                click.echo(f"❌ 错误: 文件不存在: {report_source}")
                return
            
            report_analysis = self.financial_report_analyzer.analyze(stock_code, report_source)
            
            if report_analysis:
                self._display_financial_analysis(report_analysis)
            else:
                click.echo("❌ 财报分析失败")
                
        except Exception as e:
            self.logger.error(f"财报分析失败: {str(e)}")
            click.echo(f"❌ 错误: {str(e)}")
            
    def _display_financial_analysis(self, analysis: FinancialReportAnalysis):
        """显示财报分析结果"""
        click.echo("\n" + "="*50)
        click.echo("📈 财务报告分析结果")
        click.echo("="*50)
        
        click.echo("\n📊 关键指标:")
        for metric, value in analysis.key_metrics.items():
            click.echo(f"- {metric}: {value}")
            
        click.echo("\n📈 增长分析:")
        click.echo(analysis.growth_analysis)
        
        click.echo("\n⚠️ 风险因素:")
        for risk in analysis.risk_factors:
            click.echo(f"- {risk}")
            
        click.echo("\n💡 投资建议:")
        click.echo(analysis.recommendations)
        
        click.echo("\n📝 总结:")
        click.echo(analysis.summary)
        
        click.echo("\n" + "="*50) 