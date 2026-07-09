"""
Groq 기반 LLM 클라이언트 (Qwen 모델).

기존 OpenAI/GPT 기반 호출을 Groq로 대체한다.
서비스키는 GROQ_API_KEY 환경변수 또는 .env 의 groq_api_key 로 주입한다.
"""
from typing import Any, Dict, List, Optional
import asyncio

from app.core.config import settings

try:
    from groq import Groq
except ImportError:  # pragma: no cover
    Groq = None


class LLMNotConfigured(Exception):
    pass


def get_client() -> "Groq":
    if Groq is None:
        raise LLMNotConfigured(
            "groq 패키지가 설치되지 않았습니다. pip install groq"
        )
    key = (settings.groq_api_key or "").strip()
    if not key:
        # groq 라이브러리가 자동으로 GROQ_API_KEY 환경변수를 읽도록 함
        return Groq()
    return Groq(api_key=key)


async def chat(
    messages: List[Dict[str, str]],
    temperature: float = 0.6,
    max_completion_tokens: int = 4096,
    top_p: float = 0.95,
    reasoning_effort: str = "default",
) -> str:
    """Groq 채팅 완료(비스트리밍)를 호출하고 텍스트를 반환한다."""
    client = get_client()

    def _call():
        resp = client.chat.completions.create(
            model=settings.groq_model,
            messages=messages,
            temperature=temperature,
            max_completion_tokens=max_completion_tokens,
            top_p=top_p,
            reasoning_effort=reasoning_effort,
            stream=False,
            stop=None,
        )
        return resp.choices[0].message.content or ""

    return await asyncio.to_thread(_call)


async def complete(prompt: str, **kwargs) -> str:
    """단일 프롬프트를 사용하는 편의 래퍼."""
    return await chat([{"role": "user", "content": prompt}], **kwargs)
