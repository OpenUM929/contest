import httpx, json, sys, time

BASE = "http://localhost:8000"
client = httpx.Client()
WELFARE_ID = "d61a34b3-0761-4eee-8566-bdeee09af14c"

def check(label, resp):
    if resp.status_code >= 400:
        print(f"[FAIL] {label}: {resp.status_code}")
        print(resp.text[:500])
        return False
    print(f"[OK] {label}: {resp.status_code}")
    return True

# 1. 사용자 생성
r1 = client.post(f"{BASE}/chat/users", json={"user_type": "elder", "nickname": "test_elder", "welfare_id": WELFARE_ID})
if not check("1. user_create", r1): sys.exit(1)
user_id = r1.json()["user_id"]

# 2. 주제 발행 (mixed + choices)
choices_json = {
    "schema_version": "1.0",
    "question_type": "mixed",
    "questions": [
        {
            "id": "q1",
            "type": "choice",
            "text": "남대문 시장에 가본 적이 있으신가요?",
            "target_age": "elderly",
            "allow_multiple": False,
            "has_other": True,
            "options": [
                {"id": "opt_1", "label": "네, 자주 갔어요", "value": "yes"},
                {"id": "opt_2", "label": "가끔 갔었어요", "value": "sometimes"},
                {"id": "opt_3", "label": "아니오, 들어만 봤어요", "value": "no"},
                {"id": "opt_other", "label": "기타 (직접 말씀해 주세요)", "value": "OTHER", "is_other": True},
            ],
        },
        {
            "id": "q2",
            "type": "narrative",
            "text": "시장에서 가장 기억에 남는 순간을 이야기해 주세요.",
            "target_age": "elderly",
            "placeholder": "그날의 이야기를 들려주세요...",
            "guidelines": ["누구와 함께", "무엇을 했는지"],
        },
    ],
}
r2 = client.post(f"{BASE}/welfare/topics/publish", json={
    "title": "1960년대 남대문 시장",
    "description": "분주한 장터",
    "media_type": "text",
    "question_type": "mixed",
    "welfare_id": WELFARE_ID,
    "ai_question": "테스트 질문",
    "choices": choices_json,
})
if not check("2. publish_topic (mixed + choices)", r2): sys.exit(1)
topic_id = r2.json()["topic_id"]

# 3. AI 질문 생성 (choice) -- fallback
r3 = client.post(f"{BASE}/welfare/topics/generate-questions", json={
    "title": "1960년대 남대문 시장",
    "description": "분주한 장터",
    "media_type": "text",
    "target_age": "elderly",
    "question_type": "choice",
    "question_count": 1,
})
if not check("3. generate-questions (choice)", r3): sys.exit(1)
qset_choice = r3.json()
# API key 없으면 DEFAULT_FALLBACK(narrative) 반환 -- 이것도 정상
assert "question_type" in qset_choice
print(f"    question_type={qset_choice['question_type']}, questions={len(qset_choice['questions'])}")

# 4. AI 질문 생성 (mixed) -- fallback
r4 = client.post(f"{BASE}/welfare/topics/generate-questions", json={
    "title": "1960년대 남대문 시장",
    "description": "분주한 장터",
    "media_type": "text",
    "target_age": "elderly",
    "question_type": "mixed",
    "narrative_count": 1,
    "choice_count": 1,
})
if not check("4. generate-questions (mixed)", r4): sys.exit(1)
qset_mixed = r4.json()
assert "question_type" in qset_mixed
print(f"    question_type={qset_mixed['question_type']}, questions={len(qset_mixed['questions'])}")

# 5. validate-questions (valid)
r5 = client.post(f"{BASE}/welfare/topics/validate-questions", json={"question_set": choices_json})
if not check("5. validate-questions (valid)", r5): sys.exit(1)
assert r5.json()["valid"] == True

# 6. validate-questions (invalid)
bad_json = {"schema_version": "1.0", "question_type": "mixed", "questions": []}
r6 = client.post(f"{BASE}/welfare/topics/validate-questions", json={"question_set": bad_json})
if not check("6. validate-questions (invalid)", r6): sys.exit(1)
assert r6.json()["valid"] == False
print(f"    errors={r6.json()['errors']}")

# 7. save-draft
r7 = client.post(f"{BASE}/welfare/topics/save-draft", json={
    "welfare_id": WELFARE_ID,
    "title": "draft test",
    "question_type": "mixed",
    "question_set": choices_json,
})
if not check("7. save-draft", r7): sys.exit(1)
proposal_id = r7.json()["proposal_id"]

# 8. surveys/current
r8 = client.get(f"{BASE}/welfare/surveys/current")
if not check("8. surveys/current", r8): sys.exit(1)
assert any(t["topic_id"] == topic_id for t in r8.json())
print(f"    topics={len(r8.json())}")

# 9. chat/message (choice q1)
with client.stream("POST", f"{BASE}/chat/message", json={
    "user_id": user_id,
    "message": "네, 자주 갔어요",
    "question_id": "q1",
    "selected_option_id": "opt_1",
    "selected_option_label": "네, 자주 갔어요",
}) as r9:
    if not check("9. chat/message (choice q1)", r9): sys.exit(1)

# 10. chat/message (narrative q2)
with client.stream("POST", f"{BASE}/chat/message", json={
    "user_id": user_id,
    "message": "어머니 손을 잡고 갔던 그날이 기억나요. 생선을 사서 집에 돌아가는 길이 참 좋았습니다.",
    "question_id": "q2",
}) as r10:
    if not check("10. chat/message (narrative q2)", r10): sys.exit(1)

# 11. survey responses
r11 = client.get(f"{BASE}/welfare/surveys/{topic_id}/responses")
if not check("11. survey responses", r11): sys.exit(1)
responses = r11.json()["responses"]
assert len(responses) == 2, f"expected 2, got {len(responses)}"
print(f"    responses={len(responses)} (q1 choice + q2 narrative)")

# 12. analytics
r12 = client.get(f"{BASE}/welfare/surveys/{topic_id}/analytics")
if not check("12. analytics", r12): sys.exit(1)
analytics = r12.json()
assert analytics["total_respondents"] == 1
print(f"    total_respondents={analytics['total_respondents']}")
for q in analytics["questions"]:
    print(f"    [{q['type']}] {q['text'][:30]}...")

# 13. clone
r13 = client.post(f"{BASE}/welfare/surveys/{topic_id}/clone")
if not check("13. clone survey", r13): sys.exit(1)
print(f"    proposal_id={r13.json()['proposal_id']}")

# 14. edit (add option, change label)
edited_choices = json.loads(json.dumps(choices_json))
edited_choices["questions"][0]["options"].insert(1, {"id": "opt_new", "label": "새로 추가한 보기", "value": "new"})
edited_choices["questions"][0]["options"][0]["label"] = "네, 자주 갔어요 (수정됨)"
r14 = client.put(f"{BASE}/welfare/surveys/{topic_id}/edit", json={
    "title": "1960년대 남대문 시장 (수정됨)",
    "choices": edited_choices,
})
if not check("14. edit survey (add option + change label)", r14): sys.exit(1)

# 15. save template
r15 = client.post(f"{BASE}/welfare/survey-templates", json={
    "welfare_id": WELFARE_ID,
    "name": "my mixed template",
    "question_set": edited_choices,
})
if not check("15. save template", r15): sys.exit(1)

# 16. list templates
r16 = client.get(f"{BASE}/welfare/survey-templates?welfare_id={WELFARE_ID}")
if not check("16. list templates", r16): sys.exit(1)
print(f"    templates={len(r16.json())}")

print("\n" + "="*50)
print("Phase 1 test ALL PASSED")
print("="*50)
client.close()
