token = "sk-0e29f2cd26b4465484b4b26f9e8a479a";
# 业务空间模型调用请参考文档传入workspace信息: https://help.aliyun.com/document_detail/2746874.html

# For prerequisites running the following sample, visit https://help.aliyun.com/document_detail/611472.html
from http import HTTPStatus
import dashscope

dashscope.api_key = token


def call_with_prompt():
    dashscope.api_key = token
    response = dashscope.Generation.call(
        model=dashscope.Generation.Models.qwen_turbo,
        prompt='帮我分析一下中国银行的财报，就你知道的最新场景'
    )

    # 如果调用成功，则打印模型的输出
    if response.status_code == HTTPStatus.OK:
        print(response)
        print(response.message)
    # 如果调用失败，则打印出错误码与失败信息
    else:
        print(response.code)
        print(response.message)


def call_with_llama3_messages():
    messages = [{'role': 'system', 'content': '你是一个非常牛逼的金融咨询师，你要协助我走向财富自由.'},
                {'role': 'user', 'content': '帮我分析一下中国银行的财报，就你知道的最新信息'}]

    response = dashscope.Generation.call(
        model='llama3-70b-instruct',
        messages=messages,
        result_format='message',  # set the result to be "message" format.
    )
    if response.status_code == HTTPStatus.OK:
        print(response)
    else:
        print('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
            response.request_id, response.status_code,
            response.code, response.message
        ))


if __name__ == '__main__':
    # call_with_prompt()
    call_with_llama3_messages()
