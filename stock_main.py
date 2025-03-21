import click
from trade.cli.commands import CLI
from trade.config.settings import Settings
from typing import List
import sys
from pathlib import Path

from trade.core.backtest_engine import BacktestEngine
from trade.core.data_fetcher import DataFetcher
import click.core
from datetime import datetime
import os
import numpy as np

from trade.utils.data_processor import DataProcessor

# 设置代理
os.environ['https_proxy'] = 'http://127.0.0.1:7890'
os.environ['http_proxy'] = 'http://127.0.0.1:7890'
os.environ['all_proxy'] = 'socks5://127.0.0.1:7890'

# 创建一个 CLI 组来管理多个命令
@click.group()
def cli():
    """股票分析预测工具"""
    pass

# 将现有的 main 函数改名为 analyze 并注册到 cli 组
@cli.command(name='analyze')
@click.argument('stock_codes', nargs=-1)
@click.option('--period', default='3mo', help='数据周期: 1d/5d/1mo/3mo/6mo/1y/2y/5y/10y/ytd/max')
@click.option('--interval', default='1d', help='数据间隔: 1m/2m/5m/15m/30m/60m/90m/1h/1d/5d/1wk/1mo/3mo')
@click.option('--predict-days', default=5, help='预测天数')
@click.option('--analysis-type',
              type=click.Choice(['all', 'predict', 'turtle', 'sentiment', 'ai', 'financial', 'showData']),
              default='all',
              help='分析类型:全部/预测/海龟/情绪/AI/财报')
@click.option('--report-url', help='财报PDF的URL（仅在分析类型为financial时需要）')
def analyze(stock_codes: List[str], period: str, interval: str, predict_days: int, 
           analysis_type: str, report_url: str):
    """分析股票数据
    示例:
    python main.py analyze AAPL GOOGL --period 6mo --interval 1d
    """
    try:
        click.echo("="*50)
        click.echo(f"开始分析任务 - 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo(f"分析参数:")
        click.echo(f"- 股票代码: {', '.join(stock_codes)}")
        click.echo(f"- 周期: {period}")
        click.echo(f"- 间隔: {interval}")
        click.echo(f"- 预测天数: {predict_days}")
        click.echo(f"- 分析类型: {analysis_type}")
        click.echo("="*50)
        # 初始化必要的目录
        click.echo("\n[1/2] 初始化系统...")
        Settings.init_directories()
        cli = CLI()
        # 获取股票数据
        click.echo("\n[2/2] 获取股票数据...")
        results = cli.data_fetcher.fetch_multiple_stocks(
            stock_codes=stock_codes,
            period=period,
            interval=interval
        )
        if not results:
            click.echo("\n❌ 错误: 未能获取到任何股票数据")
            sys.exit(1)
        # 执行分析
        total_stocks = len(results)
        for idx, stock_data in enumerate(results, 1):
            stock_code = stock_data.code
            click.echo(f"\n{'='*50}")
            click.echo(f"分析股票 {stock_code} ({idx}/{total_stocks})")
            click.echo(f"{'='*50}")
            
            predictions = signals = sentiment = report = financial_analysis = backtest_results = None

            if analysis_type in ['all', 'showData']:
                click.echo("\n🔮 获取数据")
                processor = DataProcessor()
                processed_data = processor.calculate_technical_indicators(stock_data)

                print(processed_data)

                last_row = processed_data.iloc[-1].to_dict()

                # 格式化数据（处理numpy类型和日期）
                formatted_data = {}
                for key, value in last_row.items():
                    if isinstance(value, np.float64):
                        formatted_data[key] = float(value)
                    elif isinstance(value, np.int64):
                        formatted_data[key] = int(value)
                    elif isinstance(value, datetime):
                        formatted_data[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        formatted_data[key] = value

                # 使用JSON格式美化输出
                import json
                click.echo("\n📊 最新一条数据:"+ f'{stock_codes} code:')
                click.echo(json.dumps(formatted_data, indent=2, ensure_ascii=False))
                click.echo("✅ 获取数据展示完成")
                click.echo("✅ 获取数据展示完成")

            if analysis_type in ['all', 'predict']:
                click.echo("\n🔮 执行预测分析...")
                cli.lstm_predictor.train(stock_data)
                predictions = cli.lstm_predictor.predict(stock_data, days_ahead=predict_days)
                click.echo("✅ 预测分析完成")

            if analysis_type in ['all', 'turtle']:
                click.echo("\n🐢 执行海龟策略分析...")
                signals = cli.turtle_strategy.analyze(stock_data)
                click.echo("✅ 海龟策略分析完成")

                # 修改：直接使用原始数据，通过过滤时间来创建新的数据框
                filtered_data = stock_data
                filtered_data.data = filtered_data.data[filtered_data.data.index <'2024-01-01']
                
                # 在analyze方法中调用回测
                backtest_engine = BacktestEngine(initial_capital=1000000)
                backtest_results = backtest_engine.run_backtest(stock_data, cli.turtle_strategy)
            if analysis_type in ['all', 'sentiment']:
                click.echo("\n😊 执行情绪分析...")
                sentiment = cli.sentiment_analyzer.analyze(stock_data)
                click.echo("✅ 情绪分析完成")

            if analysis_type in ['all', 'ai']:
                click.echo("\n🤖 执行AI分析...")
                report = cli.ai_analyzer.analyze(stock_data)
                click.echo("✅ AI分析完成")

            if analysis_type in ['all', 'financial'] and report_url:
                click.echo("\n📊 执行财报分析...")
                financial_analysis = cli.financial_report_analyzer.analyze(stock_code, report_url)
                if financial_analysis:
                    click.echo("✅ 财报分析完成")
                else:
                    click.echo("❌ 财报分析失败")

            # 展示该股票的分析结果汇总
            display_analysis_summary(
                stock_code, 
                predictions, 
                signals, 
                sentiment, 
                report,
                financial_analysis,
                backtest_results
            )

            # 如果是 'all' 类型，直接保存已经计算的结果
            #if analysis_type == 'all':
                # click.echo("\n📊 保存分析结果...")
                # cli.excel_writer.write_predictions(predictions)
                # cli.excel_writer.write_trade_signals(signals)
                # cli.excel_writer.write_sentiment_analysis([sentiment])
                # cli.excel_writer.write_ai_reports([report])
                # click.echo("✅ 结果保存完成")

        click.echo("\n🎉 所有分析任务已完成!")
        click.echo(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo("="*50)

    except KeyboardInterrupt:
        click.echo("\n❌ 程序被用户中断")
        sys.exit(0)
    except Exception as e:
        click.echo(f"\n❌ 发生错误: {str(e)}")
        sys.exit(1)

def display_analysis_summary(stock_code: str, predictions, signals, sentiment, report, financial_analysis=None, backtest_results=None):
    """展示分析结果汇总"""
    click.echo("\n" + "="*50)
    click.echo(f"📊 {stock_code} 分析结果汇总")
    click.echo("="*50)
    
    if predictions is not None:
        click.echo("\n🔮 llm 预测分析结果:")
        try:
            # 如果predictions是PredictionResult对象列表
            if isinstance(predictions, list) and predictions:
                latest_pred = predictions[-1]
                first_pred = predictions[0]
                trend = "上涨 📈" if latest_pred.predicted_price > first_pred.predicted_price else "下跌 📉"
                prices = [p.predicted_price for p in predictions]
                click.echo(f"- 未来5天预测趋势: {trend}")
                click.echo(f"- 预测价格区间: {min(prices):.2f} - {max(prices):.2f}")
                click.echo(f"- 置信度: {latest_pred.confidence:.2%}")
            else:
                click.echo("- 无有效预测数据")
        except Exception as e:
            click.echo(f"- 预测数据处理出错: {str(e)}")
    
    if signals is not None:
        click.echo("\n🐢 海龟策略信号:")
        try:
            if isinstance(signals, list) and signals:
                latest_signal = signals[-1]
                action_map = {
                    'BUY': "买入 ⬆️",
                    'SELL': "卖出 ⬇️",
                    'HOLD': "持有 ➡️"
                }
                # 修改信号显示格式
                click.echo("- 历史信号列表:")
                for signal in signals:
                    click.echo(f"  • {signal.date}: {action_map.get(signal.action, '无信号')} "
                             f"@ ¥{signal.price:.2f} - {signal.reason}")
                
                click.echo(f"\n- 最新交易日期: {latest_signal.date}")
                click.echo(f"- 最新交易信号: {action_map.get(latest_signal.action, '无信号')}")
                click.echo(f"- 交易价格: {latest_signal.price:.2f}")
                click.echo(f"- 信号原因: {latest_signal.reason}")
                
                # 添加回测结果显示
                click.echo("\n📊 策略回测结果:")
                results = backtest_results
                click.echo(f"- 总收益率: {results['total_return']:.2%}")
                click.echo(f"- 年化收益率: {results['annual_return']:.2%}")
                click.echo(f"- 夏普比率: {results['sharpe_ratio']:.2f}")
                click.echo(f"- 最大回撤: {results['max_drawdown']:.2%}")
                click.echo(f"- 总交易次数: {results['total_trades']}")
                click.echo(f"- 胜率: {results['win_rate']:.2%}")
                click.echo(f"- 最终资金: ¥{results['final_value']:,.2f}")
            else:
                click.echo("- 无交易信号")
        except Exception as e:
            click.echo(f"- 信号处理出错: {str(e)}")
    
    if sentiment is not None:
        click.echo("\n😊 情绪分析结果:")
        sentiment_score = sentiment.sentiment_score if hasattr(sentiment, 'sentiment_score') else 0
        sentiment_level = "积极 🟢" if sentiment_score > 0.5 else "消极 🔴" if sentiment_score < -0.5 else "中性 🟡"
        click.echo(f"- 市场情绪: {sentiment_level}")
        if hasattr(sentiment, 'keywords') and sentiment.keywords:
            click.echo(f"- 热门关键词: {', '.join(sentiment.keywords[:3])}")
    
    if report is not None:
        click.echo("\n🤖 AI分析建议:")
        if isinstance(report, dict):
            recommendation = report.get('recommendation', '无建议')
            risk_level = report.get('risk_level', '未知')
        else:
            recommendation = getattr(report, 'recommendation', '无建议')
            risk_level = getattr(report, 'risk_level', '未知')
        click.echo(f"- 投资建议: {recommendation}")
        click.echo(f"- 风险等级: {risk_level}")
    
    if financial_analysis is not None:
        click.echo("\n📈 财报分析结果:")
        try:
            # 显示关键指标
            click.echo("\n📊 关键财务指标:")
            for metric, value in financial_analysis.key_metrics.items():
                click.echo(f"- {metric}: {value}")
            
            # 显示增长分析
            if financial_analysis.growth_analysis:
                click.echo("\n📈 增长分析:")
                click.echo(f"- {financial_analysis.growth_analysis}")
            
            # 显示风险因素
            if financial_analysis.risk_factors:
                click.echo("\n⚠️ 风险因素:")
                for risk in financial_analysis.risk_factors:
                    click.echo(f"- {risk}")
            
            # 显示投资建议
            if financial_analysis.recommendations:
                click.echo("\n💡 财报投资建议:")
                click.echo(f"- {financial_analysis.recommendations}")
            
        except Exception as e:
            click.echo(f"- 财报数据处理出错: {str(e)}")
    
    click.echo("\n" + "="*50)

#雅虎财经 https://finance.yahoo.com/quote/159740.SZ/
if __name__ == "__main__":
    # 添加调试信息
    print("程序开始运行...")
    
    try:
        # 使用 sys.argv 来模拟命令行参数
        sys.argv = [
            sys.argv[0],
            "analyze",
            # "AAPL",
            #"159740.SZ",
            #"515100.SS",
            "513130.SS", # 恒生科技etf
            "510310.SS", # 沪深300 etf
            "--period", "max",
            "--interval", "1d",
            "--predict-days", "5",
            "--analysis-type", "showData",
        ]
        print(f"命令行参数: {sys.argv}")
        
        # 添加调试信息
        print("开始执行 cli()...")
        cli()
        print("程序执行完成")
        
    except Exception as e:
        print(f"发生错误: {str(e)}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)
