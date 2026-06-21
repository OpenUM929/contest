"""Claude / OpenAI / Gemini 통합 호출 서비스.

복지사가 등록한 API 키로 지정 제공자를 호출한다. SDK 의존성을 줄이기 위해
OpenAI/Gemini는 httpx로 REST API를 직접 호출하고, Claude만 기존에 설치된
anthropic SDK를 재사용한다. 모든 실패는 None을 반환하여 호출자가 fallback을
처리하도록 한다.
"""
from __future__ import annotations

import logging

import httpx

logger = logging.getLogger("ium.ai_provider")

_TIMEOUT = 30.0
_CLAUDE_MODEL = "claude-sonnet-4-6"
_OPENAI_MODEL = "gpt-4o"
_GEMINI_MODEL = "gemini-2.0-flash"


async def call_ai(
    prompt: str,
    provider: str,
    api_key: str,
    max_tokens: int = 1500,
    system_prompt: str | None = None,
) -> str | None:
    """provider("claude"|"openai"|"gemini")로 텍스트를 생성한다. 실패 시 None."""
    if not api_key:
        return None
    try:
        if provider == "claude":
            return await _call_claude(prompt, api_key, max_tokens, system_prompt)
        if provider == "openai":
            return await _call_openai(prompt, api_key, max_tokens, system_prompt)
        if provider == "gemini":
            return await _call_gemini(prompt, api_key, max_tokens, system_prompt)
        logger.warning(f"[AIProvider] 알 수 없는 provider: {provider}")
        return None
    except Exception as e:
        logger.warning(f"[AIProvider] {provider} 호출 실패: {e!r}")
        return None


async def _call_claude(
    prompt: str, api_key: str, max_tokens: int, system_prompt: str | None
) -> str | None:
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=api_key, timeout=_TIMEOUT, max_retries=1)
    try:
        kwargs = {
            "model": _CLAUDE_MODEL,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        msg = await client.messages.create(**kwargs)
        if msg.content and msg.content[0].text:
            return msg.content[0].text
        return None
    except anthropic.AuthenticationError:
        logger.warning("[AIProvider] Claude 인증 실패(키 오류)")
        return None


async def _call_openai(
    prompt: str, api_key: str, max_tokens: int, system_prompt: str | None
) -> str | None:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {"model": _OPENAI_MODEL, "max_tokens": max_tokens, "messages": messages}
    headers = {"Authorization": f"Bearer {api_key}"}
    url = "https://api.openai.com/v1/chat/completions"

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        for attempt in range(2):  # 429 시 1회 재시도
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code in (401, 403):
                logger.warning("[AIProvider] OpenAI 인증 실패(키 오류)")
                return None
            if resp.status_code == 429 and attempt == 0:
                continue
            if resp.status_code >= 400:
                logger.warning(f"[AIProvider] OpenAI 오류 {resp.status_code}: {resp.text[:200]}")
                return None
            data = resp.json()
            choices = data.get("choices") or []
            if choices:
                return (choices[0]["message"].get("content") or "").strip() or None
            return None
    return None


async def _call_gemini(
    prompt: str, api_key: str, max_tokens: int, system_prompt: str | None
) -> str | None:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{_GEMINI_MODEL}:generateContent?key={api_key}"
    )
    payload: dict = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": max_tokens},
    }
    if system_prompt:
        payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        for attempt in range(2):  # 429 시 1회 재시도
            resp = await client.post(url, json=payload)
            if resp.status_code in (401, 403):
                logger.warning("[AIProvider] Gemini 인증 실패(키 오류)")
                return None
            if resp.status_code == 429 and attempt == 0:
                continue
            if resp.status_code >= 400:
                logger.warning(f"[AIProvider] Gemini 오류 {resp.status_code}: {resp.text[:200]}")
                return None
            data = resp.json()
            candidates = data.get("candidates") or []
            if candidates:
                parts = candidates[0].get("content", {}).get("parts") or []
                text = "".join(p.get("text", "") for p in parts).strip()
                return text or None
            return None
    return None
