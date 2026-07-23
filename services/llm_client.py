import aiohttp
from typing import List, Dict
from config import GROQ_API_KEY

class LLMClient:
    """
    Клиент для Groq Cloud API (бесплатно).
    """
    def __init__(self, model: str = "llama3-70b-8192"):
        self.api_key = GROQ_API_KEY
        self.model = "llama-3.3-70b-versatile"
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def generate_response(self, messages: List[Dict[str, str]]) -> str:
        if not self.api_key:
            raise ValueError("GROQ_API_KEY не задан в .env")

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.base_url, headers=self.headers, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    error_text = await resp.text()
                    raise Exception(f"Groq API error {resp.status}: {error_text}")