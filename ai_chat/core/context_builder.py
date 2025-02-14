from typing import Optional, Tuple, Dict
from ai_chat.models.character import Character
from ai_chat.models.chat_history import ChatHistory

class ContextBuilder:
    def build_2v2_context(self,
                         team1_characters: Tuple[Character, Character],
                         team2_characters: Tuple[Character, Character],
                         chat_history: ChatHistory,
                         topic: str,
                         zhihu_context: Optional[Dict] = None) -> str:
        """构建2v2对话上下文"""
        context = []
        speaker1, speaker2 = team1_characters
        listener1, listener2 = team2_characters
        
        # 添加基本场景说明
        context.append(f"""这是一个2v2的小组讨论。
你们正在讨论主题：{topic}

你所在的小组：
- {speaker1.name}（{speaker1.occupation}）和 {speaker2.name}（{speaker2.occupation}）

对话的另一组：
- {listener1.name}（{listener1.occupation}）和 {listener2.name}（{listener2.occupation}）
""")

        # 添加知乎上下文（如果有）
        if zhihu_context:
            context.append("\n相关知乎讨论：")
            context.append(f"问题：{zhihu_context['title']}")
            if zhihu_context.get('answers'):
                context.append("部分回答：")
                for i, answer in enumerate(zhihu_context['answers'], 1):
                    context.append(f"回答{i}：{answer[:200]}...")  # 限制长度
        
        # 添加历史对话上下文
        recent_history = chat_history.get_recent_context(speaker1.name)
        if recent_history:
            context.append("\n最近的对话历史：")
            context.append(recent_history)
        
        return "\n".join(context)

    def build_context(self,
                     speaker_character: Character,
                     listener_character: Character,
                     chat_history: ChatHistory,
                     topic: Optional[str] = None) -> str:
        """构建一对一对话上下文"""
        context = []
        
        # 添加基本场景说明
        context.append(f"""你正在与 {listener_character.name}（{listener_character.occupation}）进行对话。
        
当前话题：{topic if topic else '自由交流'}

请用中文回复，保持对话自然流畅。要注意：
1. 体现你的专业背景和个性特点
2. 与对方进行有意义的交流
3. 保持友好和专业的对话氛围
""")
        
        # 添加历史对话上下文
        recent_history = chat_history.get_recent_context(speaker_character.name)
        if recent_history:
            context.append("\n最近的对话历史：")
            context.append(recent_history)
        
        return "\n".join(context) 