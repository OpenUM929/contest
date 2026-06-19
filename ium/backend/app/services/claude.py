from typing import AsyncGenerator
from app.config import settings

_anthropic_client = None

def _get_client():
    global _anthropic_client
    if _anthropic_client is None:
        import anthropic
        # 일시적 네트워크 끊김(읽기 타임아웃, 연결 리셋)에 자동 재시도하도록
        # 타임아웃과 재시도 횟수를 명시한다. 기본값은 재시도가 적어 장애가 잦다.
        _anthropic_client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key,
            timeout=60.0,
            max_retries=3,
        )
    return _anthropic_client

ELDER_SYSTEM = """\
당신은 '이음'이라는 AI 동반자입니다. 어르신과 문화·기억에 대한 따뜻한 대화를 나눕니다.

규칙:
- 항상 존댓말 사용 (하세요, 드릴게요)
- 한 번에 1~2문장, 짧고 명확하게
- 사용자 말을 먼저 공감한 뒤 질문
- 슬픈 내용은 자연스럽게 수용, 과도한 반응 금지
- 의료·법률 조언 금지

이번 주 주제: {topic_title}
주제 설명: {topic_description}
"""

YOUTH_SYSTEM = """\
당신은 '이음'이라는 AI 창작 동반자입니다. 청년과 문화를 주제로 생각과 감정을 나눕니다.

규칙:
- 자연스럽고 편안한 말투
- 판단·평가 없이 있는 그대로 수용
- 쓴 내용에서 흥미로운 부분을 찾아 대화 이어가기
- 익명이 보장된다는 점을 자연스럽게 상기
- 창작 참여에 부담 없음을 자주 언급

이번 주 주제: {topic_title}
"""

CRISIS_KEYWORDS = {
    "high": ["죽고 싶", "사라지고 싶", "없어지고 싶", "죽어버릴", "끝내고 싶"],
    "medium": ["힘들어서 못", "아무도 없", "혼자서는 못", "포기하고"],
    "low": ["외롭", "아무도 모르", "지쳐"],
}


def detect_crisis_level(text: str) -> str | None:
    for level in ("high", "medium", "low"):
        if any(kw in text for kw in CRISIS_KEYWORDS[level]):
            return level
    return None


async def _opencode_chat_fallback(system: str, messages: list[dict]) -> str:
    """Claude 스트리밍 실패 시 OpenCode로 비스트리밍 응답을 받아 한 번에 돌려준다."""
    if not settings.opencode_api_key:
        return ""
    import httpx
    oc_messages = [{"role": "system", "content": system}] + messages
    async with httpx.AsyncClient() as client:
        # max_tokens는 의도적으로 보내지 않는다(추론 모델이 예산을 reasoning에 소진해 빈 본문 반환).
        resp = await client.post(
            f"{settings.opencode_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.opencode_api_key}"},
            json={
                "model": settings.opencode_model or "big-pickle",
                "messages": oc_messages,
            },
            timeout=120.0,
        )
        data = resp.json()
        if "choices" in data and data["choices"]:
            return (data["choices"][0]["message"].get("content") or "").strip()
    return ""


async def stream_chat(
    user_type: str,
    topic: dict,
    history: list[dict],
    user_message: str,
    crisis_level: str | None = None,
) -> AsyncGenerator[str, None]:
    import logging
    logger = logging.getLogger("ium.claude")

    # 주제 미발행(None) 시에도 일반 대화가 가능하도록 방어
    topic = topic or {}
    system_template = ELDER_SYSTEM if user_type == "elder" else YOUTH_SYSTEM
    system = system_template.format(
        topic_title=topic.get("title", ""),
        topic_description=topic.get("description", ""),
    )
    if crisis_level:
        system += f"\n- 위기 키워드 감지 시 응답 맨 앞에 [CRISIS:{crisis_level.upper()}] 태그 삽입 (시스템 전용)"
    else:
        system += "\n- 위기 키워드 감지 시 응답 맨 앞에 [CRISIS] 태그 삽입 (시스템 전용)"

    messages = history[-10:] + [{"role": "user", "content": user_message}]

    CRISIS_PREFIX = f"[CRISIS:{crisis_level.upper()}]" if crisis_level else "[CRISIS]"
    buffer = ""
    prefix_done = False
    is_crisis = False
    yielded_any = False  # 본문을 한 글자라도 내보냈는지 (폴백 중복 방지)

    def _strip_prefix(text: str) -> str:
        # 누적 버퍼에서 CRISIS_PREFIX를 제거한다.
        if text.startswith(CRISIS_PREFIX):
            return text[len(CRISIS_PREFIX):].lstrip()
        return text

    try:
        client = _get_client()
        async with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=300,
            system=system,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                if not prefix_done:
                    buffer += text
                    if len(buffer) >= len(CRISIS_PREFIX):
                        prefix_done = True
                        is_crisis = buffer.startswith(CRISIS_PREFIX)
                        buffer = _strip_prefix(buffer)
                        if buffer:
                            yielded_any = True
                            yield buffer
                            buffer = ""
                else:
                    yielded_any = True
                    yield text

            # 스트림이 CRISIS_PREFIX 길이보다 짧게 끝난 경우 처리
            if not prefix_done:
                buffer = _strip_prefix(buffer)
                if buffer:
                    yielded_any = True
                    yield buffer
    except Exception as e:
        logger.warning(f"[Claude] 채팅 스트리밍 실패: {e}")
        # 아직 아무것도 못 내보냈으면 OpenCode로 폴백 시도
        if not yielded_any:
            try:
                fallback = await _opencode_chat_fallback(system, messages)
                fallback = _strip_prefix(fallback)
                if fallback:
                    yielded_any = True
                    yield fallback
            except Exception as e2:
                logger.error(f"[OpenCode] 채팅 폴백도 실패: {e2}")
        # 폴백까지 실패했거나 스트림 도중 끊긴 경우, 사용자에게 안내 문구
        if not yielded_any:
            yield "죄송해요, 지금 잠시 연결이 원활하지 않네요. 잠시 후 다시 말씀해 주시겠어요?"

    if crisis_level == "high":
        yield "\n\n지금 많이 힘드신가요? 정신건강 위기상담전화 1393으로 언제든 도움받으실 수 있습니다."


async def generate_text(prompt: str, max_tokens: int = 1500) -> str:
    """Claude API 우선, 실패 시 OpenCode API fallback"""
    import logging
    logger = logging.getLogger("ium.claude")
    
    # 1. Claude API 시도
    if settings.anthropic_api_key:
        try:
            client = _get_client()
            msg = await client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text
        except Exception as e:
            logger.warning(f"[Claude] API 호출 실패, OpenCode fallback: {e}")
    
    # 2. OpenCode API fallback
    if settings.opencode_api_key:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                # max_tokens는 의도적으로 보내지 않는다.
                # OpenCode의 기본 모델(big-pickle→deepseek 계열)은 추론(reasoning) 모델이라,
                # max_tokens를 낮게 주면 그 예산을 reasoning_content에 모두 소진하고
                # 실제 content가 빈 문자열로 돌아온다(finish_reason=length).
                # 주제 생성용 _call_opencode_chat과 동일하게 캡을 두지 않아 본문이 생성되도록 한다.
                resp = await client.post(
                    f"{settings.opencode_base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {settings.opencode_api_key}"},
                    json={
                        "model": settings.opencode_model or "big-pickle",
                        "messages": [{"role": "user", "content": prompt}],
                    },
                    timeout=120.0,
                )
                data = resp.json()
                if "choices" in data and data["choices"]:
                    content = data["choices"][0]["message"].get("content") or ""
                    if not content.strip():
                        finish = data["choices"][0].get("finish_reason")
                        logger.error(f"[OpenCode] 빈 content 반환 (finish_reason={finish})")
                        raise ValueError("OpenCode 응답 content가 비어 있습니다")
                    return content
                else:
                    logger.error(f"[OpenCode] 응답 형식 오류: {data}")
                    raise ValueError("OpenCode API 응답 형식 오류")
        except Exception as e:
            logger.error(f"[OpenCode] API 호출 실패: {e}")
            raise
    
    raise ValueError("LLM API 키가 설정되지 않았습니다 (ANTHROPIC_API_KEY 또는 OPENCODE_API_KEY)")
