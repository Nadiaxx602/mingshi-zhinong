"""DeepSeek API 封装"""
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
)

MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")


def call_llm(system_prompt: str, user_input: str,
             temperature: float = 0.3,
             json_mode: bool = True) -> dict:
    """
    调用 DeepSeek。强制 JSON 输出便于下游解析。
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]

    kwargs = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = _client.chat.completions.create(**kwargs)
    content = response.choices[0].message.content

    if json_mode:
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            return {"_parse_error": str(e), "_raw": content}
    return {"text": content}
