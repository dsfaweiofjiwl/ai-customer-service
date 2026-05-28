from typing import AsyncGenerator
from openai import AsyncOpenAI
import config

_client = AsyncOpenAI(
    api_key=config.DEEPSEEK_API_KEY,
    base_url=config.DEEPSEEK_BASE_URL,
)


async def chat_stream(
    messages: list[dict],
    temperature: float = config.TEMPERATURE,
    max_tokens: int = config.MAX_TOKENS,
) -> AsyncGenerator[str, None]:
    response = await _client.chat.completions.create(
        model=config.DEEPSEEK_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )
    async for chunk in response:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content
