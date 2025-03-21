import numpy as np
import pandas as pd

from ..models.entities import StockData
from ..utils.data_processor import DataProcessor
from ..utils.logger import Logger

class BacktestEngine:
    """
    回测引擎类
    用于执行策略回测并计算各项指标
    """
    def __init__(self, initial_capital: float = 1000000):
        self.logger = Logger()
        self.data_processor = DataProcessor()
        self.initial_capital = initial_capital
        self.commission_rate = 0.0003  # 佣金费率 0.03%
        self.min_commission = 5  # 最低佣金 5元
        self.transfer_fee_rate = 0.00001  # 过户费 0.001%
        self.stamp_duty_rate = 0.0005  # 印花税 0.05%，仅卖出收取
        self.reset()
        
    def reset(self):
        """重置回测状态"""
        self.cash = self.initial_capital
        self.current_position = 0
        self.positions = []
        self.portfolio_values = []
        
    def _calculate_trading_cost(self, amount: float, is_buy: bool) -> float:
        """
        计算交易成本
        
        Args:
            amount: 交易金额
            is_buy: 是否为买入交易
            
        Returns:
            float: 总交易成本
        """
        # 计算佣金
        commission = max(amount * self.commission_rate, self.min_commission)
        # 计算过户费
        transfer_fee = amount * self.transfer_fee_rate
        # 计算印花税（仅卖出时收取）
        stamp_duty = amount * self.stamp_duty_rate if not is_buy else 0
        
        return commission + transfer_fee + stamp_duty

    def run_backtest(self, stock_data: StockData, strategy) -> dict:
        """
        执行回测
        
        Args:
            stock_data: 股票数据
            strategy: 交易策略对象
            
        Returns:
            dict: 回测结果指标
        """
        try:
            df = self.data_processor.prepare_turtle_data(stock_data)
            trades = []
            
            # 遍历每个交易日进行回测
            for i in range(1, len(df)):
                current_row = df.iloc[i]
                prev_row = df.iloc[i-1]
                date = df.index[i]
                
                # 使用策略检查信号
                entry_signal = strategy._check_entry_signal(current_row, prev_row)
                exit_signal = strategy._check_exit_signal(current_row, prev_row)
                
                # 执行交易 - 使用100%仓位
                if entry_signal and self.current_position == 0:
                    # 计算可用资金（考虑交易成本）
                    estimated_cost = self.cash
                    trading_cost = self._calculate_trading_cost(estimated_cost, True)
                    actual_cash = self.cash - trading_cost
                    
                    # 买入信号，使用扣除手续费后的现金
                    position_size = actual_cash / current_row['Close']
                    cost = position_size * current_row['Close']
                    total_cost = cost + trading_cost
                    
                    self.current_position = position_size
                    self.cash = self.cash - total_cost
                    
                    self.logger.info(f"""
买入信号 - {date.strftime('%Y-%m-%d')}:
    买入价格: {current_row['Close']:.2f}
    买入数量: {position_size:.2f}
    交易成本: {trading_cost:.2f}
    总成本: {total_cost:.2f}
    剩余现金: {self.cash:.2f}
""")
                    trades.append({
                        'date': date,
                        'action': 'BUY',
                        'price': current_row['Close'],
                        'size': position_size,
                        'cost': cost,
                        'trading_cost': trading_cost,
                        'total_cost': total_cost
                    })
                
                elif exit_signal and self.current_position > 0:
                    # 卖出信号，清空所有仓位
                    gross_revenue = self.current_position * current_row['Close']
                    trading_cost = self._calculate_trading_cost(gross_revenue, False)
                    net_revenue = gross_revenue - trading_cost
                    
                    self.logger.info(f"""
卖出信号 - {date.strftime('%Y-%m-%d')}:
    卖出价格: {current_row['Close']:.2f}
    卖出数量: {self.current_position:.2f}
    交易成本: {trading_cost:.2f}
    总收入(含费用): {gross_revenue:.2f}
    净收入(扣除费用): {net_revenue:.2f}
    当前现金: {self.cash:.2f}
""")
                    trades.append({
                        'date': date,
                        'action': 'SELL',
                        'price': current_row['Close'],
                        'size': self.current_position,
                        'gross_revenue': gross_revenue,
                        'trading_cost': trading_cost,
                        'net_revenue': net_revenue
                    })
                    self.cash = net_revenue
                    self.current_position = 0
                
                # 记录每日组合价值
                portfolio_value = self.cash + (self.current_position * current_row['Close'])
                self.portfolio_values.append({
                    'date': date,
                    'value': portfolio_value,
                    'cash': self.cash,
                    'position': self.current_position
                })
            
            return self._calculate_metrics(trades)
            
        except Exception as e:
            self.logger.error(f"回测执行过程出错: {str(e)}")
            raise
            
    def _calculate_metrics(self, trades: list) -> dict:
        """计算回测指标"""
        if not self.portfolio_values:
            return {}
            
        portfolio_values = pd.DataFrame(self.portfolio_values)
        portfolio_values.set_index('date', inplace=True)
        
        # 计算收益率
        initial_value = portfolio_values['value'].iloc[0]
        final_value = portfolio_values['value'].iloc[-1]
        total_return = (final_value - initial_value) / initial_value
        
        # 计算每日收益率
        daily_returns = portfolio_values['value'].pct_change().dropna()
        
        # 计算年化收益率
        days = (portfolio_values.index[-1] - portfolio_values.index[0]).days
        annual_return = (1 + total_return) ** (365/days) - 1
        
        # 计算夏普比率
        risk_free_rate = 0.03
        excess_returns = daily_returns - risk_free_rate/252
        sharpe_ratio = np.sqrt(252) * excess_returns.mean() / daily_returns.std()
        
        # 计算最大回撤
        cummax = portfolio_values['value'].cummax()
        drawdown = (portfolio_values['value'] - cummax) / cummax
        max_drawdown = drawdown.min()
        
        # 计算交易统计
        winning_trades = [t for t in trades if t['action'] == 'SELL' and 
                         t['net_revenue'] > trades[trades.index(t)-1]['total_cost']]
        total_sell_trades = len([t for t in trades if t['action'] == 'SELL'])
        
        # 计算总交易成本
        total_trading_cost = sum(t['trading_cost'] for t in trades)
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': total_sell_trades,
            'winning_trades': len(winning_trades),
            'win_rate': len(winning_trades) / total_sell_trades if total_sell_trades > 0 else 0,
            'final_value': final_value,
            'total_trading_cost': total_trading_cost,
            'trades': trades
        } 