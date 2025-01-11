from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from ai_chat.models.character import Character
from ai_chat.models.chat_history import ChatHistory
from ai_chat.core.ollama_client import OllamaClient
from ai_chat.core.context_builder import ContextBuilder
from ai_chat.core.community_manager import CommunityManager
from ai_chat.core.zhihu_crawler import ZhihuCrawler
import random

class ChatManager:
    def __init__(self):
        self.community = CommunityManager()
        self.chat_history = ChatHistory()
        self.ollama_client = OllamaClient()
        self.context_builder = ContextBuilder()
        self.zhihu_crawler = ZhihuCrawler()
        self.last_conversation_time: Dict[tuple, datetime] = {}
    
    async def get_zhihu_context(self, topic: str) -> Optional[Dict]:
        """获取相关的知乎内容"""
        try:
            hot_topics = await self.zhihu_crawler.get_hot_topics()
            # 选择一个相关话题
            for hot_topic in hot_topics:
                if any(keyword in hot_topic['title'].lower() for keyword in topic.lower().split()):
                    answers = await self.zhihu_crawler.get_answers(hot_topic['url'])
                    return {
                        'title': hot_topic['title'],
                        'answers': answers
                    }
            return None
        except Exception as e:
            print(f"获取知乎内容时出错: {e}")
            return None
    
    async def generate_2v2_conversation(self, 
                                      team1: Tuple[str, str],
                                      team2: Tuple[str, str],
                                      topic: str,
                                      interval_seconds: int = 15) -> Optional[Tuple[str, str]]:
        """生成2v2对话
        
        Returns:
            Optional[Tuple[str, str]]: 返回一个元组 (speaker, response)，如果无法生成对话则返回 None
        """
        speaker1, speaker2 = team1
        listener1, listener2 = team2
        
        # 检查是否可以开始新对话
        conv_key = (speaker1, speaker2, listener1, listener2)
        if not self.can_start_conversation(conv_key, interval_seconds):
            return None
        
        # 获取知乎上下文
        zhihu_context = await self.get_zhihu_context(topic)
        
        # 构建上下文
        context = self.context_builder.build_2v2_context(
            team1_characters=(self.community.members[speaker1], self.community.members[speaker2]),
            team2_characters=(self.community.members[listener1], self.community.members[listener2]),
            chat_history=self.chat_history,
            topic=topic,
            zhihu_context=zhihu_context
        )
        
        # 随机选择发言者
        speaker = random.choice([speaker1, speaker2])
        
        # 生成回复
        response = await self.ollama_client.generate_response(
            prompt=context,
            system_prompt=self.community.members[speaker].to_context_prompt()
        )
        
        # 记录对话和时间
        if response:
            self.chat_history.add_message(speaker, f"{listener1}, {listener2}", response)
            self.last_conversation_time[conv_key] = datetime.now()
            return (speaker, response)
        
        return None
    
    def can_start_conversation(self, 
                             conv_key: tuple,
                             interval_seconds: int) -> bool:
        """检查是否可以开始新的对话
        
        Args:
            conv_key: 对话的键值，可以是(speaker, listener)或(speaker1, speaker2, listener1, listener2)
            interval_seconds: 对话间隔时间
        """
        last_time = self.last_conversation_time.get(conv_key)
        
        if last_time is None:
            return True
            
        time_passed = datetime.now() - last_time
        return time_passed.total_seconds() >= interval_seconds
    
    def _get_conversation_key(self, speaker: str, listener: str) -> tuple:
        """生成对话键值"""
        return (speaker, listener)
    
    async def generate_conversation(self, 
                                  speaker: str, 
                                  listener: str, 
                                  topic: Optional[str] = None,
                                  interval_seconds: int = 15) -> Optional[str]:
        """生成两个角色之间的对话"""
        if speaker not in self.community.members or listener not in self.community.members:
            raise ValueError("角色不存在")
        
        # 检查是否可以开始新对话
        if not self.can_start_conversation(self._get_conversation_key(speaker, listener), interval_seconds):
            return None
            
        # 构建上下文
        context = self.context_builder.build_context(
            speaker_character=self.community.members[speaker],
            listener_character=self.community.members[listener],
            chat_history=self.chat_history,
            topic=topic
        )
        
        # 生成回复
        response = await self.ollama_client.generate_response(
            prompt=context,
            system_prompt=self.community.members[speaker].to_context_prompt()
        )
        
        # 记录对话和时间
        if response:
            self.chat_history.add_message(speaker, listener, response)
            conv_key = self._get_conversation_key(speaker, listener)
            self.last_conversation_time[conv_key] = datetime.now()
            
        return response 