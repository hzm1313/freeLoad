import click
from trade.cli.commands import CLI
from trade.config.settings import Settings
from typing import List
import sys
from pathlib import Path
from trade.core.data_fetcher import DataFetcher
import click.core
from datetime import datetime

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
              type=click.Choice(['all', 'predict', 'turtle', 'sentiment', 'ai']),
              default='all',
              help='分析类型:全部/预测/海龟/情绪/AI')
def analyze(stock_codes: List[str], period: str, interval: str, predict_days: int, analysis_type: str):
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
            if analysis_type in ['all', 'predict']:
                click.echo("\n🔮 执行预测分析...")
                click.echo("- 正在加载预测模型...")
                stock_data = cli.data_fetcher.fetch_stock_data(stock_code)
                cli.lstm_predictor.train(stock_data)
                cli.lstm_predictor.predict(stock_data, days_ahead=predict_days)
                click.echo("✅ 预测分析完成")

            if analysis_type in ['all', 'turtle']:
                click.echo("\n🐢 执行海龟策略分析...")
                click.echo("- 计算技术指标...")
                stock_data = cli.data_fetcher.fetch_stock_data(stock_code)
                cli.turtle_strategy.analyze(stock_data)
                click.echo("✅ 海龟策略分析完成")

            if analysis_type in ['all', 'sentiment']:
                click.echo("\n😊 执行情绪分析...")
                click.echo("- 获取市场情绪数据...")
                stock_data = cli.data_fetcher.fetch_stock_data(stock_code)
                cli.sentiment_analyzer.analyze(stock_data)
                click.echo("✅ 情绪分析完成")

            if analysis_type in ['all', 'ai']:
                click.echo("\n🤖 执行AI分析...")
                click.echo("- 正在进行深度学习分析...")
                stock_data = cli.data_fetcher.fetch_stock_data(stock_code)
                cli.ai_analyzer.analyze(stock_data)
                click.echo("✅ AI分析完成")

            if analysis_type == 'all':
                click.echo("\n📊 执行全面分析...")
                click.echo("- 整合所有分析结果...")
                stock_data = cli.data_fetcher.fetch_stock_data(stock_code)
                cli.lstm_predictor.train(stock_data)
                predictions = cli.lstm_predictor.predict(stock_data)
                signals = cli.turtle_strategy.analyze(stock_data)
                sentiment = cli.sentiment_analyzer.analyze(stock_data)
                report = cli.ai_analyzer.analyze(stock_data)
                # 保存结果
                cli.excel_writer.write_predictions(predictions)
                cli.excel_writer.write_trade_signals(signals)
                cli.excel_writer.write_sentiment_analysis([sentiment])
                cli.excel_writer.write_ai_reports([report])
                click.echo("✅ 全面分析完成")
        click.echo("\n"+"="*50)
        click.echo("🎉 所有分析任务已完成!")
        click.echo(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo("="*50)
    except KeyboardInterrupt:
        click.echo("\n❌ 程序被用户中断")
        sys.exit(0)
    except Exception as e:
        click.echo(f"\n❌ 发生错误: {str(e)}")
        sys.exit(1)

# 将 fetch_data 注册到 cli 组
@cli.command(name='fetch-data')
@click.argument('stock_codes', nargs=-1)
@click.option('--mode', type=click.Choice(['full', 'incremental']),
              default='incremental', help='数据获取模式：全量/增量')
def fetch_data(stock_codes: List[str], mode: str):
    """获取股票数据
    示例:
    python main.py fetch-data AAPL GOOGL --mode incremental
    """
    try:
        # 初始化数据获取器
        data_fetcher = DataFetcher()
        # 设置缓存目录
        cache_dir = Path(Settings.DATA.data_dir) / 'cache'
        for stock_code in stock_codes:
            click.echo(f"获取 {stock_code} 的{mode}数据...")
            stock_data = data_fetcher.fetch_stock_data_with_mode(
                stock_code=stock_code,
                mode=mode,
                cache_dir=cache_dir
            )
            click.echo(f"成功获取 {stock_data.name} 的数据，"
                      f"数据范围：{stock_data.data.index[0]} 到 "
                      f"{stock_data.data.index[-1]}")
    except Exception as e:
        click.echo(f"发生错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # 使用 sys.argv 来模拟命令行参数
    sys.argv = [
        sys.argv[0],
        "analyze",
        "AAPL",
        "GOOGL",
        "--period", "6mo",
        "--interval", "1d",
        "--predict-days", "5",
        "--analysis-type", "all"
    ]
    cli()
