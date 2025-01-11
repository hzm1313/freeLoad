from dataclasses import dataclass
from typing import List, Dict, Set

@dataclass
class Character:
    name: str
    occupation: str
    hobbies: List[str]
    background: str
    personality: str
    goals: List[str]
    relationships: Dict[str, str]
    memory: List[Dict]
    current_partners: Set[str] = None  # 当前对话伙伴
    
    def __post_init__(self):
        self.current_partners = set()
    
    def to_context_prompt(self) -> str:
        """将角色信息转换为提示词格式"""
        return f"""
        你是 {self.name}。
        职业：{self.occupation}
        爱好：{', '.join(self.hobbies)}
        背景：{self.background}
        性格：{self.personality}
        目标：{', '.join(self.goals)}
        
        请始终以这个角色的身份进行对话，保持角色设定的一致性。
        在对话中要体现你的职业背景、性格特点和个人爱好。
        """ 