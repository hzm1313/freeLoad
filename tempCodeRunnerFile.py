import ollama

# 初始化对话历史
messages = []

# 定义用户输入函数
def user_input():
    return input("用户: ")

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

# 主对话循环
print("欢迎进行对话！输入'退出'结束对话。")
while True:
    user_message = user_input()
    if user_message.lower() == '退出':
        print("对话结束。再见！")
        break
    model_response(user_message)