import httpx, json, sys

BASE = "http://localhost:8000"

# 1. 사용자 생성
r1 = httpx.post(f"{BASE}/chat/users", json={"user_type": "elder", "nickname": "테스트어르신"})
print("users:", r1.status_code, r1.json())
user_id = r1.json()["user_id"]

# 2. 주제 발행
r2 = httpx.post(f"{BASE}/welfare/topics/publish", json={
    "title": "테스트 주제",
    "description": "설명",
    "media_type": "text",
    "question_type": "mixed",
    "welfare_id": "",
    "ai_question": "테스트 질문입니다",
})
print("publish:", r2.status_code, r2.json())
topic_id = r2.json()["topic_id"]

# 3. chat/message with question_id (survey_response 저장 테스트)
# 스트리밍 응답이므로 stream=True로 요청 후 바로 닫음
with httpx.Client() as client:
    with client.stream("POST", f"{BASE}/chat/message", json={
        "user_id": user_id,
        "message": "저는 시장에서 생선을 샀어요",
        "question_id": "q1",
        "selected_option_id": "opt_1",
        "selected_option_label": "채소와 생선 좌판",
    }) as r3:
        print("chat message:", r3.status_code)

# 4. survey_responses 조회
r4 = httpx.get(f"{BASE}/welfare/surveys/{topic_id}/responses")
print("responses:", r4.status_code, r4.json())

# 5. generate-questions (폴백 테스트)
r5 = httpx.post(f"{BASE}/welfare/topics/generate-questions", json={
    "title": "1960년대 남대문 시장",
    "description": "분주한 장터",
    "media_type": "text",
    "target_age": "elderly",
    "question_type": "mixed",
    "narrative_count": 1,
    "choice_count": 1,
})
print("generate-questions:", r5.status_code, r5.json())

# 6. validate-questions
r6 = httpx.post(f"{BASE}/welfare/topics/validate-questions", json={
    "question_set": r5.json(),
})
print("validate-questions:", r6.status_code, r6.json())

# 7. current surveys
r7 = httpx.get(f"{BASE}/welfare/surveys/current")
print("current:", r7.status_code, r7.json())
