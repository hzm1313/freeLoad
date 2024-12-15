# 使用pipeline作为高级助手
from transformers import pipeline
import os

# 设置代理环境变量
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

# 创建文本生成管道
# pipe = pipeline("text-generation", model="AdaptLLM/finance-chat")
pipe = pipeline("text-generation", model="AdaptLLM/finance-chat")

# 定义专家对话函数
def expert_dialogue(prompt, num_turns=3):
    experts = ["金融专家", "医疗专家", "数学专家"]
    conversation = []
    for i in range(num_turns):
        for expert in experts:
            expert_prompt = f"{expert}的观点（请竭尽全力辩驳）：{prompt}"
            response = pipe(expert_prompt, max_length=150, num_return_sequences=1)[0]['generated_text']
            conversation.append(f"回合 {i+1}, {expert}:\n{response}\n")
        prompt = "基于以上观点，继续讨论世界杯谁可能会赢。"
    return "\n".join(conversation)

# 示例使用
initial_prompt = "根据你的专业知识，谁最有可能赢得下一届世界杯？请提供论据。"
dialogue = expert_dialogue(initial_prompt)
print(dialogue)