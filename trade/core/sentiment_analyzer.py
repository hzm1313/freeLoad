import requests
import jieba
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime
from collections import Counter
from ..models.entities import StockData, MarketSentiment
from ..utils.logger import Logger
from ..config.settings import Settings
import json

class SentimentAnalyzer:
    def __init__(self):
        self.logger = Logger()
        self._init_sentiment_dict()
        
    def _init_sentiment_dict(self):
        """初始化情感词典"""
        # 这里可以加载自定义的情感词典
        self.positive_words = set(['利好', '上涨', '突破', '增长', '盈利', 'positive', 'bullish', 'breakthrough', 'growth', 'profit'])
        self.negative_words = set(['利空', '下跌', '跌破', '亏损', '风险', 'negative', 'bearish', 'breakdown', 'loss', 'risk'])

    def analyze(self, stock_data: StockData) -> MarketSentiment:
        """分析股票的市场情绪"""
        try:
            # 获取新闻数据
            news_data = self._fetch_news(stock_data.code)
            
            # 分析情感得分和热度
            sentiment_score, hot_degree = self._analyze_sentiment(news_data)
            
            # 生成新闻摘要
            news_summary = self._generate_summary(news_data)
            
            # 提取关键词
            keywords = self._extract_keywords(news_data)
            
            return MarketSentiment(
                code=stock_data.code,
                date=datetime.now(),
                sentiment_score=sentiment_score,
                hot_degree=hot_degree,
                news_summary=news_summary,
                keywords=keywords
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment: {str(e)}")
            raise
    
    def _fetch_news(self, stock_code: str) -> List[Dict]:
        """获取股票相关新闻
        
        Args:
            stock_code: 股票代码
            
        Returns:
            List[Dict]: 包含新闻数据的列表，每条新闻包含标题、内容、发布时间和来源
        """
        # 当前使用的 continue 对外开放的一个服务
        # todo 未来可以抽象其他的开放服务，例如 mind search / 找到 新浪财经、东方财富的 api
        try:
            # 构建请求
            url = "https://proxy-server-blue-l6vsfbzhba-uw.a.run.app/web"
            headers = {"Content-Type": "application/json"}
            data = {
                "query": f"{stock_code} 股票新闻",
                "n": 5  # 获取5条新闻
            }
            
            # 发送请求
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()  # 检查响应状态
            
            # 解析响应
            news_list = response.json()
            
            # 转换为标准格式
            formatted_news = []
            for news in news_list:
                formatted_news.append({
                    'title': news.get('name', '无标题'),
                    'content': news.get('content', '无内容'),
                    'publish_time': datetime.now(),  # API没有提供时间，使用当前时间
                    'source': news.get('description', '未知来源')
                })
            
            self.logger.info(f"Successfully fetched {len(formatted_news)} news items for {stock_code}")
            return formatted_news
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"网络请求错误: {str(e)}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析错误: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"获取{stock_code}的新闻时发生错误: {str(e)}")
            return []
    
    def _analyze_sentiment(self, news_data: List[Dict]) -> Tuple[float, float]:
        """分析新闻情感和热度"""
        if not news_data:
            return 0.0, 0.0
            
        total_score = 0
        for news in news_data:
            words = jieba.lcut(news['content'])
            pos_count = sum(1 for word in words if word in self.positive_words)
            neg_count = sum(1 for word in words if word in self.negative_words)
            total_score += (pos_count - neg_count) / (pos_count + neg_count + 1)
        
        sentiment_score = total_score / len(news_data)
        hot_degree = len(news_data) / 100  # 简化的热度计算
        
        return sentiment_score, min(hot_degree, 1.0)
    
    def _generate_summary(self, news_data: List[Dict]) -> str:
        """生成新闻摘要"""
        if not news_data:
            return "无相关新闻"
            
        # 简单示例：返回最新的新闻标题
        return news_data[0]['title']
    
    def _extract_keywords(self, news_data: List[Dict]) -> List[str]:
        """提取关键词"""
        if not news_data:
            return []
            
        # 合并所有新闻内容
        all_content = ' '.join(news['content'] for news in news_data)
        
        # 分词并统计词频
        words = jieba.lcut(all_content)
        word_count = Counter(words)
        
        # 过滤停用词并返回前5个关键词
        stop_words = set(['的', '了', '和', '是', '在'])
        keywords = [word for word, _ in word_count.most_common(10) 
                   if word not in stop_words]
        
        return keywords[:5] 