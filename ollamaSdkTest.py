import ollama
import random

# 初始化对话历史
messages = []

# 定义模型响应函数
def model_response(user_message):
    messages.append({'role': 'user', 'content': user_message})
    stream = ollama.chat(
        model='llama3.1',
        messages=messages,
        stream=True,
    )
    
    print("AI助手: ", end='', flush=True)
    full_response = ""
    for chunk in stream:
        content = chunk['message']['content']
        print(content, end='', flush=True)
        full_response += content
    print()  # 换行
    messages.append({'role': 'assistant', 'content': full_response})
    return full_response

# 生成下一个问题的函数
def generate_next_question(previous_response):
    prompt = f"基于以下回答，生成一个相关的深入金融话题问题：\n\n{previous_response}\n\n新问题："
    return model_response(prompt).strip()

print("欢迎来到自动金融对话！按Ctrl+C随时结束对话。")

# 初始问题
current_question = "什么是股票市场？"

try:
    while True:
        print(f"\n用户: {current_question}")
        response = model_response(current_question)
        current_question = generate_next_question(response)
except KeyboardInterrupt:
    print("\n\n对话已结束。谢谢使用！")