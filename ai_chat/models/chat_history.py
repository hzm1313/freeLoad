from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass
class Message:
    sender: str
    receiver: str
    content: str
    timestamp: datetime

class ChatHistory:
    def __init__(self):
        self.messages: List[Message] = []
    
    def add_message(self, sender: str, receiver: str, content: str):
        message = Message(
            sender=sender,
            receiver=receiver,
            content=content,
            timestamp=datetime.now()
        )
        self.messages.append(message)
    
    def get_recent_context(self, character_name: str, limit: int = 10) -> str:
        """获取指定角色的最近对话历史"""
        relevant_messages = [
            msg for msg in self.messages 
            if msg.sender == character_name or msg.receiver == character_name
        ][-limit:]
        
        context = ""
        for msg in relevant_messages:
            context += f"{msg.sender} 对 {msg.receiver} 说: {msg.content}\n"
        return context 