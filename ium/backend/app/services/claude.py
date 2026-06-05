from typing import AsyncGenerator
from app.config import settings

_anthropic_client = None

def _get_client():
    global _anthropic_client
    if _anthropic_client is None:
        import anthropic
        _anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _anthropic_client

ELDER_SYSTEM = """\
당신은 '이음'이라는 AI 동반자입니다. 어르신과 문화·기억에 대한 따뜻한 대화를 나눕니다.

규칙:
- 항상 존댓말 사용 (하세요, 드릴게요)
- 한 번에 1~2문장, 짧고 명확하게
- 사용자 말을 먼저 공감한 뒤 질문
- 슬픈 내용은 자연스럽게 수용, 과도한 반응 금지
- 의료·법률 조언 금지
- 위기 키워드 감지 시 응답 맨 앞에 [CRISIS] 태그 삽입 (시스템 전용)

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
- 위기 키워드 감지 시 응답 맨 앞에 [CRISIS] 태그 삽입 (시스템 전용)

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


async def stream_chat(
    user_type: str,
    topic: dict,
    history: list[dict],
    user_message: str,
) -> AsyncGenerator[str, None]:
    system_template = ELDER_SYSTEM if user_type == "elder" else YOUTH_SYSTEM
    system = system_template.format(
        topic_title=topic.get("title", ""),
        topic_description=topic.get("description", ""),
    )

    messages = history[-10:] + [{"role": "user", "content": user_message}]

    CRISIS_PREFIX = "[CRISIS]"
    buffer = ""
    prefix_done = False
    is_crisis = False

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
                    if is_crisis:
                        buffer = buffer[len(CRISIS_PREFIX):].lstrip()
                    if buffer:
                        yield buffer
                        buffer = ""
            else:
                yield text

        # 스트림이 CRISIS_PREFIX 길이보다 짧게 끝난 경우 처리
        if not prefix_done:
            is_crisis = buffer.startswith(CRISIS_PREFIX)
            if is_crisis:
                buffer = buffer[len(CRISIS_PREFIX):].lstrip()
            if buffer:
                yield buffer

    if is_crisis:
        yield "\n\n지금 많이 힘드신가요? 정신건강 위기상담전화 1393으로 언제든 도움받으실 수 있습니다."


async def generate_text(prompt: str, max_tokens: int = 1500) -> str:
    client = _get_client()
    msg = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text
