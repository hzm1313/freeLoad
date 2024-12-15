from openai import OpenAI, DefaultHttpxClient

client = OpenAI(
    # Or use the `OPENAI_BASE_URL` env var
    base_url="http://localhost:11434"
)
client.api_key = "test"


response = client.chat("测试")

print(response)
