import aiohttp
from typing import Dict, Any

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        
    async def generate_response(self, 
                              prompt: str, 
                              model: str = "llama2",
                              system_prompt: str = "") -> str:
        """调用Ollama API生成回复"""
        url = f"{self.base_url}/api/generate"
        
        # 添加中文提示
        system_prompt = f"""请使用中文回复。
{system_prompt}

注意事项：
1. 始终使用中文进行对话
2. 保持自然的对话语气
3. 回答要简洁明了，每次回复控制在100字以内
4. 表达要得体、专业
"""
        
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    response.raise_for_status()
                    result = await response.json()
                    return result["response"]
        except Exception as e:
            print(f"调用Ollama API时出错: {e}")
            return "" 