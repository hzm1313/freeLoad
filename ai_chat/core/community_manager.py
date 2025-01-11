import json
import random
import os
from typing import List, Tuple, Dict
from pathlib import Path
from ai_chat.models.character import Character

class CommunityManager:
    def __init__(self, config_path: str = None):
        self.members: Dict[str, Character] = {}
        self.topics: List[str] = []
        self.active_discussions: List[Tuple[str, str, str, str]] = []
        
        # 如果没有提供配置路径，使用默认路径
        if config_path is None:
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(current_dir, "config", "characters", "community_members.json")
        
        self.load_config(config_path)
    
    def load_config(self, config_path: str):
        """加载社区配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except FileNotFoundError:
            print(f"配置文件不存在: {config_path}")
            print("创建默认配置...")
            config = self.create_default_config(config_path)
                
        for member in config['members']:
            character = Character(
                name=member['name'],
                occupation=member['occupation'],
                hobbies=member['hobbies'],
                background=member['background'],
                personality=member['personality'],
                goals=member['goals'],
                relationships={},
                memory=[]
            )
            self.members[member['name']] = character
            
        self.topics = config['discussion_topics']
    
    def create_default_config(self, config_path: str) -> dict:
        """创建默认配置"""
        default_config = {
            "members": [
                {
                    "name": "Alice",
                    "occupation": "软件工程师",
                    "hobbies": ["编程", "读书", "弹吉他"],
                    "background": "在一家科技公司工作的全栈开发者，热爱开源社区",
                    "personality": "开朗、善于沟通",
                    "goals": ["学习新技术", "帮助新手程序员", "组建技术社区"]
                },
                # ... 其他成员配置 ...
            ],
            "discussion_topics": [
                "AI技术发展趋势",
                "创业机会与挑战",
                "产品设计与用户体验",
                "技术教育与学习方法",
                "开源社区发展",
                "职业发展规划",
                "技术与艺术的结合",
                "远程工作与团队协作"
            ]
        }
        
        # 确保目录存在
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # 写入默认配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=4)
        
        return default_config
    
    def get_random_topic(self) -> str:
        """随机选择一个讨论话题"""
        return random.choice(self.topics)
    
    def arrange_2v2_discussion(self) -> Tuple[Tuple[str, str], Tuple[str, str]]:
        """安排2v2讨论组合"""
        available_members = [name for name, char in self.members.items() 
                           if len(char.current_partners) == 0]
        
        if len(available_members) < 4:
            return None
        
        # 随机选择4个人
        selected = random.sample(available_members, 4)
        team1 = tuple(selected[:2])
        team2 = tuple(selected[2:])
        
        # 更新当前伙伴关系
        for name in team1:
            self.members[name].current_partners.add(team1[1] if name == team1[0] else team1[0])
        for name in team2:
            self.members[name].current_partners.add(team2[1] if name == team2[0] else team2[0])
        
        return (team1, team2)
    
    def end_discussion(self, team1: Tuple[str, str], team2: Tuple[str, str]):
        """结束讨论，清除伙伴关系"""
        for name in team1 + team2:
            self.members[name].current_partners.clear() 