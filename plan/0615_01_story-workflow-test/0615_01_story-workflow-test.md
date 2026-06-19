# 이음(以音) 스토리 워크플로우 통합 테스트 계획

> 상태: PND | 작성일: 2026-06-15 | 완료일: 미정
> 작업 유형: 통합 테스트 계획 + 수필 프롬프트 개선
> 대상 코드베이스: `C:\dev\contest\ium`

---

## 수정 이력

| 날짜 | 변경 섹션 | 변경 요약 |
|------|-----------|-----------|
| 2026-06-15 | 전체 | 최초 작성 |
| 2026-06-15 | §2-2, §3-4, §6, §7(신규) | 코드 검토 반영: API 경로 /api prefix 추가, §3 기능개선 구현완료 확인, generate_essay 버그 발견, welfare_id 전처리 필수화, 디버그 포인트 보강 |
| 2026-06-15 | §7(신규), §2-2 | `POST /api/essay/generate`에 `prompt_version` Query 파라미터 추가 (`v2` 기본값), `auto_generate_weekly_essay` v2 적용, 계획서 Step 11 API 호출 방법 수정 (Query param), §7-1 버그 수정 완료 반영 |
| 2026-06-15 | §2-2 | Step 11 검토: 기본값 `v2`로 자동 적용됨을 반영, 명시 필수 → 별도 명시 불필요로 수정 |
| 2026-06-15 | §2-2, §8(신규) | URL 정보 추가 (`login.html`, `user.html`), Known Issues 섹션 추가 (CORS, Dashboard 500, 이미지 URL, WelfareWorker 등) |

---

## 1. 목표

복지사가 주제를 발행하고, 노인/청년이 설문에 응답한 후, 복지사가 **응답 집계(선택형+서술형)를 확인**하고, 이를 바탕으로 **수필을 생성**하는 전체 워크플로우를 실제 API 호출로 검증합니다.

**핵심 개선**: 수필 생성 시 **객관식(선택형) 응답과 서술형 응답을 결합하여 사용자의 개성을 도출**하는 프롬프트(v2)를 적용합니다.

---

## 2. 테스트 개요

### 2-1. 테스트 시나리오

```
[복지사] ──주제 발행 + 설문 생성──→ [시스템]
                                              │
                                              ↓
                                    [주제 노출: 노인/청년 앱]
                                              │
        [노인A] ──선택형+서술형──→ [시스템] ──SurveyResponse 저장
        [노인B] ──서술형 2건──→ [시스템] ──SurveyResponse 저장
        [청년A] ──선택형+서술형──→ [시스템] ──SurveyResponse 저장
                                              │
                                              ↓
[복지사] ←──응답 집계 확인── [GET /welfare/surveys/{topic_id}/analytics]
         ←──개별 원문 확인── [GET /welfare/surveys/{topic_id}/responses]
                                              │
         ──수필 생성 요청──→ [POST /api/essay/generate]
                                              │
                                              ↓
[시스템] ──SurveyResponse(선택형+서술형) 수집──→ [Claude API/OpenCode Zen 수필 생성]
                                              │
                                              ↓
                                    [수필 저장 + EssayContributor 기록]
                                              │
                                              ↓
[복지사] ←──수필 조회── [GET /essay/{essay_id}]
```

### 2-2. 12단계 테스트 단계

| 단계 | 주체 | 행동 | API | 검증 포인트 |
|------|------|------|-----|-------------|
| **Step 1** | 프로그램 | 서버 상태 확인 | `GET /health` | `{"status":"ok"}` |
| **Step 2** | 복지사 | 전처리: 테스트 복지사 DB 삽입 후 UUID 획득 | DB 직접 삽입 | `welfare_id` (UUID) 확보 — **필수**: `welfare_workers` 테이블이 비어있으면 주제가 사용자에게 노출되지 않음. `demo-admin-001`은 `"admin"` 문자열 반환으로 UUID 파싱 불가 |
| **Step 3** | 복지사 | 임시 로그인 | `POST /api/auth/temp-login` | `demo-admin-001` → `user_id: "admin"` (확인용) |
| **Step 4** | 복지사 | 주제 후보 검색 | `POST /api/welfare/topics/search` | `media_type="text"` 후보 ≥ 1 |
| **Step 5** | 복지사 | AI 설문 생성 | `POST /api/welfare/topics/generate-questions` | `QuestionSet` schema v1.0 반환 |
| **Step 6** | 복지사 | 주제 + 설문 발행 | `POST /api/welfare/topics/publish` | `topic_id` + `choices` 저장 — `welfare_id`는 Step 2의 UUID 사용 |
| **Step 7** | 노인 | 임시 로그인 | `POST /api/auth/temp-login` | `demo-elder-001` → 실제 `User.id` — ⚠️ **`login.html`에서 드롭다운 선택** (`http://localhost:8000/login.html`) |
| **Step 8** | 노인 | 선택형+서술형 응답 | `POST /api/chat/message` | `SurveyResponse`에 `selected_option_label` + `narrative_text` 저장 — ⚠️ **주제가 `user.html`에 노출되어야 함** (`http://localhost:8000/user.html`) |
| **Step 9** | 청년 | 로그인+선택형+서술형 응답 | `POST /api/auth/temp-login` + `POST /api/chat/message` | `is_anonymous=true` 확인 — ⚠️ **동일하게 `login.html` → `user.html` 흐름** |
| **Step 10** | **복지사** | **응답 집계 확인** | `GET /api/welfare/surveys/{topic_id}/analytics` | **선택형 통계 + 서술형 원문 확인** |
| **Step 11** | **복지사** | **수필 생성** | `POST /api/essay/generate` (Query: `?prompt_version=v2`) | **선택형+서술형 결합 기반 수필 생성** — 기본값 `v2`로 자동 적용, 별도 명시 불필요 |
| **Step 12** | **복지사** | **수필 검증** | `GET /api/essay/{essay_id}` | **수필 내용 + contributor_cnt 확인** |

### 2-3. 응답 데이터 시나리오 (수필 생성 최소 5건)

| 사용자 | 응답 유형 | 건수 | 수필 원료 |
|--------|-----------|------|-----------|
| 노인A | 선택형(예) + 서술형 | 2건 | `selected_option_label` + `narrative_text` |
| 노인B | 서술형 2건 | 2건 | `narrative_text` |
| 청년A | 선택형(아니오) + 서술형 | 2건 | `selected_option_label` + `narrative_text` |
| **합계** | | **6건** | **수필 생성 가능** |

---

## 3. 기능 개선: 수필 프롬프트 v2

### 3-1. 문제 정의

현재 `ESSAY_PROMPT_V1`은 `SurveyResponse.narrative_text`만을 수필 원료로 사용합니다. **선택형(`choice`) 응답은 `narrative_text`가 NULL이므로 수필에 포함되지 않습니다.**

### 3-2. 개선 방향

선택형 응답(`selected_option_label`) + 서술형 응답(`narrative_text`)을 **사용자별로 결합**하여, "이 사람은 이런 선택을 했고, 그 뒤에 이런 이야기를 남겼다"는 **개성 도출**이 가능하도록 프롬프트를 개선합니다.

### 3-3. 프롬프트 v2 구조

```
[수필 작가·상담 전문가 공동 설계 프롬프트 v2.0 — 개성 도출]

당신은 세대 간 이야기를 엮는 작가입니다.
아래는 각 참여자의 **선택형 응답**과 **서술형 이야기**입니다.

[참여자 분석 지침]
- 선택형 응답: 참여자의 경향성, 가치관, 기억의 방향을 보여줍니다.
- 서술형 이야기: 그 경향성 뒤에 숨은 구체적인 삶을 보여줍니다.
- 두 가지를 결합하여 "이 사람은 이런 사람이다"를 추론하되, 
  직접 판단하지 말고 이야기에 스며들게 하세요.

[예시]
- 선택: "예 (시장에 가본 적 있다)" + 서술: "어머니가 생선을 손질해 주셨다"
  → 해석: "어떤 이는 시장의 생선을 통해 손맛과 정성을 기억한다"
- 선택: "아니오" + 서술: "나는 온라인으로만 산다"
  → 해석: "또 다른 이는 화면 속에서 세상을 만지며 편리함을 안다"

[창작 원칙]
...(기존 v1 원칙 유지)...

데이터:
{contributions}
```

### 3-4. 백엔드 수정 현황

> ✅ 코드 검토 결과, 아래 항목은 **이미 구현 완료** 상태입니다.

| 파일 | 항목 | 상태 |
|------|------|------|
| `essay.py:58` | `ESSAY_PROMPT_V2` 추가 | ✅ 완료 |
| `essay.py:104` | `_fetch_survey_responses()` — `selected_option_label` 포함 3-튜플 반환 | ✅ 완료 |
| `essay.py:96` | `_select_prompt` v2 분기 | ✅ 완료 |
| `essay.py:188` | `generate_essay` v2 분기: 사용자별 선택형+서술형 결합 | ✅ 완료 |

> ⚠️ 단, `essay.py`에 **버그 1건** 발견 → §7 참조

---

## 4. 테스트 프로그램 구조

### 4-1. 파일 위치

- **테스트 코드**: `ium/backend/test_story_workflow.py`
- **실행**: `cd C:\dev\contest\ium\backend && python test_story_workflow.py`

### 4-2. 실행 모드

- **auto**: 전체 단계를 자동으로 실행 (기본)
- 각 단계별로 **"현재 테스트 중인 단계"**와 **"해야 할 일"**을 설명 텍스트로 출력

### 4-3. 핵심 함수

```python
def main():
    """12단계 오케스트레이터"""
    # Step 1: 서버 상태 확인
    # Step 2: 테스트 복지사 DB 삽입 → welfare_id(UUID) 획득
    # Step 3: 복지사 임시 로그인 (확인용)
    # Step 4: 주제 후보 검색
    # Step 5: AI 설문 생성
    # Step 6: 주제 발행 (welfare_id=Step2 UUID 사용)
    # Step 7~9: 노인/청년 로그인 + 응답 (총 6건)
    # Step 10: 복지사 응답 집계 확인
    # Step 11: 수필 생성 (?prompt_version=v2)
    # Step 12: 수필 검증
```

### 4-4. 전처리/후처리

```python
# 전처리: 테스트용 WelfareWorker 삽입
async def insert_test_welfare_worker(temp_id, name, region):
    """테스트용 복지사를 DB에 삽입"""

# 후처리: 해당 복지사가 생성한 데이터만 삭제
async def delete_test_data_by_welfare_id(welfare_id):
    """WeeklyTopic, Essay, SurveyResponse, Conversation, SafetyAlert 중
    welfare_id가 테스트 복지사인 것만 삭제 (기존 데이터 보존)"""
```

---

## 5. LLM API 설정

| 항목 | 설정 |
|------|------|
| 현재 API | OpenCode Zen (big-pickle) |
| 향후 계획 | Claude API로 변경 예정 |
| 테스트 시 | 실제 API 호출 (모킹 없음) |

---

## 6. 디버그 포인트

| 구간 | 검증 내용 | 실패 시 |
|------|-----------|---------|
| **Step 2** | `insert_test_welfare_worker` 성공 후 UUID 반환 여부 | Step 6 publish 시 UUID 파싱 오류 |
| **Step 6** | 발행된 주제의 `choices`에 `schema_version: "1.0"` 포함 여부 | `WeeklyTopic.choices` 파싱 실패 |
| **Step 6** | 발행된 주제가 `get_active_topic()`으로 조회되는지 | Step 11 수필 생성 시 404 오류 |
| **Step 8~9** | `POST /api/chat/message` 시 `question_id` 제공 → `SurveyResponse` 동시 저장 여부 | `survey_response 저장 실패` 로그 확인 |
| **Step 10** | `analytics` 응답의 `sample_responses`에 실제 노인/청년 텍스트 존재 여부 | 수필 생성 원료 부족 |
| **Step 11** | `_fetch_survey_responses()`가 5건 이상 반환하는지 | `< 5`이면 `ValueError` → 테스트 실패 |
| **Step 11** | 선택형 응답(`selected_option_label`)이 프롬프트에 포함되는지 | `?prompt_version=v2` 누락 확인 |
| **Step 12** | `contributor_cnt` ≥ 2, 수필 본문 길이 800~1200자 | EssayContributor 기록 누락 |

---

## 7. 사전 수정 필요 사항 (코드 검토 결과)

> 테스트 실행 전 반드시 수정해야 하는 항목입니다.

### 7-1. ~~[버그] `generate_essay` 3-튜플 언패킹 오류~~ ✅ 수정 완료

**파일**: `ium/backend/app/services/essay.py`

**수정 내용** (2026-06-15):
- v1/v0 경로에서 `_fetch_survey_messages()` 반환값을 즉시 `(uid, text, None)` 3-튜플로 변환하여 전체 경로를 3-튜플로 통일
- `else` 분기의 프롬프트 구성 코드도 `(_, text, _)` 3-튜플 언패킹으로 수정

```python
# 수정 전 (버그)
rows = await _fetch_survey_messages(db, topic_id)  # 2-튜플
messages = [text for _, text in rows if text]      # 3-튜플 혼재 시 실패

# 수정 후
rows = [(uid, text, None) for uid, text in await _fetch_survey_messages(db, topic_id)]
messages = [text for _, text, _ in rows if text]
```

### 7-2. [설계] `welfare_id` 전처리 필수

`POST /api/auth/temp-login`의 `demo-admin-001`은 DB에 User를 생성하지 않고 `user_id: "admin"` 문자열을 반환합니다. `POST /api/welfare/topics/publish`의 `welfare_id` 필드는 `uuid.UUID()` 파싱을 시도하므로 이 값을 직접 사용하면 오류가 발생합니다.

**해결책**: 테스트 시작 전 `insert_test_welfare_worker()`로 실제 `WelfareWorker` 레코드를 DB에 삽입하고, 반환된 UUID를 이후 모든 단계에서 `welfare_id`로 사용합니다.

### 7-3. [설계] `POST /api/essay/generate`의 topic_id 고정 불가

수필 생성 API는 내부적으로 `get_active_topic(db)`로 현재 활성 주제를 자동 조회하며, topic_id를 파라미터로 받지 않습니다. 따라서 테스트에서 발행한 주제가 `active_week`(이번 주 월요일) 기준 활성 상태여야 합니다. 기존 활성 주제가 있으면 가장 최근 발행 주제를 우선합니다.

### 7-4. [별도 발견] `welfare.py:archive` return 누락

`GET /api/welfare/topics/archive` 핸들러(`welfare.py:1040`)의 마지막 줄에 `return archive`가 없어 `None`을 반환합니다. 이번 테스트 범위 외이지만 수정이 필요합니다.

### 7-5. [발견] `auth.py` 신규 사용자 `welfare_id` 미설정

`temp-login` 시 기존 사용자는 `welfare_id`가 NULL이면 `get_active_topic`에서 지역 매칭 실패 → 주제 미노출.

**해결**: `auth.py`에서 `WelfareWorker` 첫 번째 레코드를 자동 연결하도록 수정 + 기존 사용자 DB 업데이트.

---

## 8. Known Issues (테스트 중 발견)

> 2026-06-15 테스트 중 발견된 문제들입니다.

| # | 문제 | 위치 | 상태 | 비고 |
|---|------|------|------|------|
| 1 | **CORS** `allow_origins=["*"]` + `allow_credentials=True` 충돌 | `main.py` | ✅ 수정 완료 | 구체적 origin 목록으로 변경, 서버 재시작 필요 |
| 2 | **Dashboard 500** Internal Server Error | `welfare.py/dashboard` | 🔴 미해결 | 원인 조사 중 |
| 3 | **이미지 URL 400** 한국어 파일명 인코딩 | `minio.nculture.org` | 🔴 미해결 | 프론트엔드/백엔드 인코딩 처리 필요 |
| 4 | **WelfareWorker 미생성** | DB 초기화 | ✅ 임시 해결 | 수동 삽입 완료, `init_local_db.py` 실행 필요 |
| 5 | **User.welfare_id NULL** | `auth.py` | ✅ 수정 완료 | `auth.py` 수정 + 기존 7명 DB 업데이트 |
| 6 | **주제 region mismatch** | `save_weekly_topic` | ⚠️ 확인 필요 | `region="default"` vs 사용자 지역 매칭 |
| 7 | **수필 생성 500** | `essay.py` | 🔴 미해결 | `generate_text` API 호출 실패 원인 확인 필요 |
| 8 | **테스트 정보 미제공** | 문서 | ✅ 확인 완료 | `login.html`, `user.html` URL 추가 |
| 9 | **`native_uuid` 파라미터** 서버 크래시 | `database.py` | ✅ 수정 완료 | `native_uuid=False` 제거 |

---

## 9. 참고 문서

| 문서 | 내용 | 위치 |
|------|------|------|
| 통합 구현 계획 | 전체 파이프라인 설명 | `plan/이음_통합구현계획_20260604.md` |
| 수필 생성 파이프라인 | 수필 API 설계 | `plan/reference/pipeline-D/plan_D_essay-generation.md` |
| 복지사 대시보드 | 복지사 API 설계 | `plan/reference/pipeline-F/plan_F_welfare-worker.md` |
| 사용자 대화 | 채팅 API 설계 | `plan/reference/pipeline-B/plan_B_user-chat.md` |

---

> 계획서 저장 위치: `plan/0615_01_story-workflow-test/0615_01_story-workflow-test.md`
