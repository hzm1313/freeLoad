import aiohttp
import json
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

class ZhihuCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    async def get_hot_topics(self, limit: int = 5) -> List[Dict]:
        """获取知乎热门话题"""
        url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total"
        params = {
            'limit': limit,
            'desktop': 'true'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return [
                            {
                                'title': item['target']['title'],
                                'url': f"https://www.zhihu.com/question/{item['target']['id']}",
                                'excerpt': item['target'].get('excerpt', '')
                            }
                            for item in data['data']
                        ]
            return []
        except Exception as e:
            print(f"获取知乎话题时出错: {e}")
            return []
    
    async def get_answers(self, question_url: str, limit: int = 3) -> List[str]:
        """获取知乎问题的回答"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(question_url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        answers = []
                        for answer in soup.select('.RichContent-inner')[:limit]:
                            text = answer.get_text().strip()
                            if text:
                                answers.append(text[:500])  # 限制回答长度
                        return answers
            return []
        except Exception as e:
            print(f"获取知乎回答时出错: {e}")
            return [] 