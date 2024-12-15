import ollama

from test import extract_text_from_pdf

content = extract_text_from_pdf('/Users/zm.huang/Downloads/PF规则.pdf');
response = ollama.generate(model='llama3.1',
                           prompt='用中文总结这个 pdf 内容是什么，需要3000字的长文总结？以下是 pdf 内容 \n' + content)

print(response.get("response"))


ollama.chat()