import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
from pathlib import Path
from typing import List, Optional
from trade.config.settings import Settings
from trade.models.entities import StockData
from trade.utils.logger import Logger
import os

class DataFetcher:
    def __init__(self):
        self.logger = Logger()
        self.session = self._create_session()
        self.local_data_dir = Path("trade/data/stocks")
        self.local_data_dir.mkdir(parents=True, exist_ok=True)
        
    def _create_session(self) -> requests.Session:
        """创建请求会话"""
        session = requests.Session()
        if Settings.PROXY.enabled:
            session.proxies.update({
                'http': Settings.PROXY.http,
                'https': Settings.PROXY.https
            })
        return session
    
    def fetch_stock_data(self, stock_code: str, 
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None,
                        period: str = "3mo",
                        interval: str = "1d") -> StockData:
        """获取股票数据，优先从本地读取"""
        try:
            # 检查本地文件
            local_file = self.local_data_dir / f"{stock_code}.xlsx"
            if local_file.exists():
                self.logger.info(f"从本地读取{stock_code}数据")
                try:
                    data = pd.read_excel(local_file, index_col=0, parse_dates=True)
                    
                    # 检查数据是否需要更新
                    if not data.empty:
                        last_date = data.index[-1]
                        today = datetime.now().date()
                        
                        # 如果最后一条数据不是今天的，且是交易时间，则更新数据
                        if last_date.date() < today and self._is_trading_hours():
                            self.logger.info(f"本地数据需要更新: {stock_code}")
                            new_data = self._fetch_from_yfinance(stock_code, 
                                                               start_date=last_date + timedelta(days=1),
                                                               end_date=end_date,
                                                               period=period,
                                                               interval=interval)
                            if not new_data.empty:
                                # 合并新旧数据
                                data = pd.concat([data, new_data])
                                data = data[~data.index.duplicated(keep='last')]
                                # 保存更新后的数据
                                data.to_excel(local_file)
                        
                        return StockData(
                            code=stock_code,
                            name=self.get_stock_name(stock_code),
                            data=data,
                            last_update=datetime.now()
                        )
                except Exception as e:
                    self.logger.error(f"读取本地文件失败: {str(e)}")
                    # 如果本地文件读取失败，删除可能损坏的文件
                    local_file.unlink(missing_ok=True)
            
            # 如果本地文件不存在或读取失败，从网络获取
            self.logger.info(f"从网络获取{stock_code}数据")
            data = self._fetch_from_yfinance(stock_code, start_date, end_date, period, interval)
            
            # 保存到本地
            if not data.empty:
                try:
                    data.to_excel(local_file)
                except Exception as e:
                    self.logger.error(f"保存到本地失败: {str(e)}")
            
            return StockData(
                code=stock_code,
                name=self.get_stock_name(stock_code),
                data=data,
                last_update=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Error fetching data for {stock_code}: {str(e)}")
            raise
    
    def _fetch_from_yfinance(self, stock_code: str,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None,
                            period: str = "3mo",
                            interval: str = "1d") -> pd.DataFrame:
        """从 yfinance 获取数据并移除时区信息"""
        ticker = yf.Ticker(stock_code)
        data = ticker.history(start=start_date, end=end_date, 
                            period=period, interval=interval)
        
        # 移除时区信息
        data.index = data.index.tz_localize(None)
        return data
    
    def _is_trading_hours(self) -> bool:
        """检查当前是否是交易时间"""
        now = datetime.now()
        # 周一到周五
        if now.weekday() < 5:
            # 9:30 - 15:00 交易时间 (简化处理，实际可能需要考虑不同市场)
            current_time = now.time()
            return (current_time >= datetime.strptime("09:30", "%H:%M").time() and 
                    current_time <= datetime.strptime("15:00", "%H:%M").time())
        return False
    
    def fetch_multiple_stocks(self, stock_codes: List[str], 
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None,
                            period: str = "3mo",
                            interval: str = "1d") -> List[StockData]:
        """批量获取多只股票数据"""
        results = []
        for code in stock_codes:
            try:
                stock_data = self.fetch_stock_data(code, start_date, end_date, 
                                                 period, interval)
                results.append(stock_data)
            except Exception as e:
                self.logger.error(f"Skipping {code} due to error: {str(e)}")
                continue
        return results
    
    def update_stock_data(self, existing_data: StockData) -> StockData:
        """增量更新股票数据"""
        last_date = existing_data.data.index[-1]
        start_date = last_date + timedelta(days=1)
        
        try:
            new_data = self.fetch_stock_data(
                existing_data.code,
                start_date=start_date,
                end_date=datetime.now()
            )
            
            # 合并新旧数据
            combined_data = pd.concat([existing_data.data, new_data.data])
            combined_data = combined_data[~combined_data.index.duplicated(keep='last')]
            
            return StockData(
                code=existing_data.code,
                name=existing_data.name,
                data=combined_data,
                last_update=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Error updating data for {existing_data.code}: {str(e)}")
            return existing_data 
    
    def fetch_stock_data_with_mode(self, stock_code: str,
                                 mode: str = 'full',  # 'full' 或 'incremental'
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None,
                                 period: str = "3mo",
                                 interval: str = "1d",
                                 cache_dir: Optional[Path] = None) -> StockData:
        """
        根据指定模式获取股票数据
        
        Args:
            stock_code: 股票代码
            mode: 获取模式 - 'full'(全量) 或 'incremental'(增量)
            start_date: 开始日期
            end_date: 结束日期
            period: 周期
            interval: 时间间隔
            cache_dir: 缓存目录路径
            
        Returns:
            StockData: 股票数据对象
        """
        try:
            # 如果是增量模式，先检查本地缓存
            if mode == 'incremental' and cache_dir:
                cache_file = cache_dir / f"{stock_code}_data.parquet"
                if cache_file.exists():
                    # 读取缓存数据
                    cached_data = pd.read_parquet(cache_file)
                    last_date = pd.to_datetime(cached_data.index[-1])
                    
                    # 获取增量数据
                    start_date = last_date + timedelta(days=1)
                    end_date = end_date or datetime.now()
                    
                    if start_date >= end_date:
                        self.logger.info(f"{stock_code} 数据已是最新")
                        return StockData(
                            code=stock_code,
                            name=stock_code,  # 可以通过API获取股票名称
                            data=cached_data,
                            last_update=datetime.now()
                        )
                    
                    # 获取增量数据
                    new_data = self.fetch_stock_data(
                        stock_code,
                        start_date=start_date,
                        end_date=end_date,
                        interval=interval
                    )
                    
                    # 合并新旧数据
                    combined_data = pd.concat([cached_data, new_data.data])
                    # 去除重复数据
                    combined_data = combined_data[~combined_data.index.duplicated(keep='last')]
                    
                    # 更新缓存
                    combined_data.to_parquet(cache_file)
                    
                    return StockData(
                        code=stock_code,
                        name=new_data.name,
                        data=combined_data,
                        last_update=datetime.now()
                    )
            
            # 全量模式或没有缓存时，直接获取数据
            stock_data = self.fetch_stock_data(
                stock_code,
                start_date=start_date,
                end_date=end_date,
                period=period,
                interval=interval
            )
            
            # 如果指定了缓存目录，保存数据
            if cache_dir:
                cache_dir.mkdir(parents=True, exist_ok=True)
                cache_file = cache_dir / f"{stock_code}_data.parquet"
                stock_data.data.to_parquet(cache_file)
            
            return stock_data
            
        except Exception as e:
            self.logger.error(f"获取{stock_code}数据失败: {str(e)}")
            raise
    
    def get_stock_name(self, stock_code: str) -> str:
        """获取股票名称"""
        try:
            ticker = yf.Ticker(stock_code)
            return ticker.info.get('shortName', stock_code)
        except:
            return stock_code