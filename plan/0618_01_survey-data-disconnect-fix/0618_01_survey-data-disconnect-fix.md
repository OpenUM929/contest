> 상태: DONE | 작성일: 2026-06-18 | 최종 업데이트: 2026-06-18 (수행 완료)

---

## 0. 수행 결과 (2026-06-18)

모든 P0/P1 항목 구현 완료. 백엔드 `py_compile` OK, 대시보드 `vite build` OK(exit 0).

**연결 모델 통일**: 더미 계정도 실제 DB FK(`User.welfare_id` → `WelfareWorker.id`, `WeeklyTopic.welfare_id`)를 그대로 타도록 모든 경로를 **welfare_id 기반**으로 통일. 하드코딩 우회 없음 → 추후 DB 데이터만 교체하면 동작.

| 변경 | 파일 |
|------|------|
| `get_active_topic(welfare_id 우선 해석, 폴백 제거→None, 다중결과 first())` | `ium/backend/app/services/public_data.py` |
| `save_weekly_topic` upsert에 `welfare_id`(+`IS NULL`) 키 추가 | `ium/backend/app/services/public_data.py` |
| `chat_message`/`get_topic`/`active-topic` 호출부에 `welfare_id` 전달 | `ium/backend/app/routers/chat.py` |
| 설문응답 `topic_uuid` 없으면 400 | `ium/backend/app/routers/chat.py` |
| `available-surveys` region→welfare_id 격리(`==본인 OR IS NULL`) | `ium/backend/app/routers/chat.py` |
| `stream_chat` `topic=None` 방어 | `ium/backend/app/services/claude.py` |
| `surveys/current`·`/history`·`/analytics`에 `welfare_id` 필터/403 | `ium/backend/app/routers/welfare.py` |
| survey API에 `welfareId` 인자 전달 | `ium/dashboard/src/api/survey.ts` |
| **복지사 선택 드롭다운 추가**(Dashboard 패턴) + 자식 컴포넌트 전달 | `ium/dashboard/src/pages/SurveyManagerPage.tsx`, `components/SurveyHistory.tsx`, `components/SurveyAnalytics.tsx` |
| 주제 없음 안내 문구 개선 | `ium/backend/app/static/user.html` |

**추가 보강(검토 중 발견)**:
- `get_active_topic` 2·3단계 region 폴백도 `welfare_id IS NULL`로 제한 → 같은 지역 타 복지사 주제 노출 차단(격리 일관성).
- `SurveyManagerPage`는 부모(App.tsx)가 welfare_id를 안 넘겨 항상 빈 값이었음 → 자체 워커 선택기 추가로 해결.

# 설문 데이터 연동 불가 문제 수정 계획

---

## 1. 개요

**증상**:
- 복지사가 발행한 주제에 대해 사용자가 설문 응답해도 복지사 대시보드에 결과가 표시되지 않음
- 사용자에게 보이는 주제 제목과 복지사가 발행한 제목이 다름
- 사용자가 설문 응답을 해도 `SurveyResponse` 테이블에 저장되지 않음

**근본 원인**: 4가지 구조적 결함
1. TOPIC_POOL 폴백이 `id=None` 반환 → 응답 미저장
2. `save_weekly_topic`이 `(week, region)`만으로 upsert → 복지사끼리 덮어씀
3. 복지사 API에 `welfare_id` 필터링 누락
4. 사용자-복지사 간 주제 연결 고리 부재

---

## 2. 문제 상세 진단

### 2-1. TOPIC_POOL 폴백과 응답 손실

**파일**: `backend/app/services/public_data.py` (줄 1343-1352)

```python
# DB에 주제가 없으면 TOPIC_POOL 폴백
topic = pool[idx].copy()
topic["id"] = None          # ← DB ID 없음
```

**영향**:
- `chat.py`의 `chat_message()`에서 `if body.question_id and topic_uuid:` 조건 실패
- `SurveyResponse` 레코드 미생성
- 응답이 `Conversation`(채팅)으로만 저장 → 복지사 API가 조회 불가

**파일**: `backend/app/routers/chat.py` (줄 105-124)

```python
if body.question_id and topic_uuid:
    survey_resp = SurveyResponse(topic_id=topic_uuid, ...)
    db.add(survey_resp)
```

### 2-2. save_weekly_topic의 복지사 무시 upsert

**파일**: `backend/app/services/public_data.py` (줄 1230-1237)

```python
existing = await db.execute(
    select(WeeklyTopic).where(
        WeeklyTopic.active_week == monday,
        WeeklyTopic.region == topic_data.get("region", "default"),
    )
)
```

**영향**: `welfare_id` 불문하고 `(week, region)`으로 upsert. 같은 지역의 다른 복지사가 발행하거나 스케줄러가 발행하면 기존 주제 덮어쓰기 발생.

### 2-3. 복지사 API에 welfare_id 필터 누락

**파일**: `backend/app/routers/welfare.py`

| 엔드포인트 | 문제 |
|-----------|------|
| `GET /surveys/current` (줄 779-800) | `welfare_id` 필터 없음 |
| `GET /surveys/history` (줄 803-824) | `welfare_id` 필터 없음 |
| `GET /surveys/{topic_id}/analytics` (줄 1014-1106) | 소유권 검증 없음 |

**영향**: 복지사가 자신의 대시보드에서 다른 복지사 또는 중앙 기본 주제의 통계를 보게 됨.

### 2-4. 데이터 흐름 요약

```
[김복지]                    [김할머니]
  │                            │
  ▼                            ▼
주제 발행 ──→ DB (WeeklyTopic)    │
  │                 │            get_active_topic()
  │                 │              │
  │                 │     DB 조회 실패 (지역 불일치 / 없음)
  │                 │              │
  │                 │     TOPIC_POOL 폴백 (id=None)
  │                 │              │
  │                 │         설문 응답 제출
  │                 │              │
  │                 │     SurveyResponse 미생성 (topic_id=None)
  │                 │              │
  ▼                 ▼              ▼
대시보드 조회 ──→ SurveyResponse 0건 → "결과 없음"
```

---

## 3. 수정 사항

### P0 (필수, 선행)

| 항목 | 설명 | 파일 | 난이도 |
|------|------|------|--------|
| 3-0 | **`get_active_topic`이 `user.welfare_id` 우선 해석** (근본 원인 #4 해결) | `public_data.py`, `chat.py` | 중 |
| 3-1 | `get_active_topic` 폴백 완전 제거 → `None` 반환 | `public_data.py` | 하 |
| 3-2 | `save_weekly_topic`에 `welfare_id` 포함 upsert | `public_data.py` | 중 |
| 3-3 | 복지사 API에 `welfare_id` 필터 추가 | `welfare.py` | 중 |
| 3-4 | 설문 응답 저장 시 topic_id 검증 강화 | `chat.py` | 하 |
| 3-4b | `stream_chat`에 `topic=None` 전달 시 방어 처리 | `chat.py`, `claude.py` | 하 |

### P1 (함께 수정)

| 항목 | 설명 | 파일 | 난이도 |
|------|------|------|--------|
| 3-5 | 사용자 페이지: DB 주제 없을 때 메시지 표시 | `user.html` | 하 |
| 3-6 | 대시보드: 설문 통계 UI 추가 확인 | `Dashboard.tsx` | 중 |

---

## 4. 상세 구현

### 4-0. get_active_topic의 welfare_id 우선 해석 (근본 원인 #4)

**문제**: 현재 사용자→주제 연결은 region 기반이다 (`chat.py:73-81`).
```python
region = "default"
if user.welfare_id:
    region = (WelfareWorker.region 조회) or "default"
topic = await get_active_topic(db, region=region)   # ← region으로만 해석
```
따라서 P0-2/P0-3으로 저장·조회를 welfare_id 단위로 격리해도, 사용자는 여전히 region으로 주제를 받는다. 같은 region의 복수 복지사를 담당하는 사용자들은 동일한(임의의) 주제를 받게 되어 격리가 절반만 된다.

**추가 부작용**: P0-2가 같은 region에 복지사별 다중 주제를 허용하는 순간, `get_active_topic`의 `scalar_one_or_none()` (`public_data.py:1294`)이 2건 이상을 만나 `MultipleResultsFound` 예외를 던져 사용자 채팅 API 전체가 실패한다.

**수정**: `get_active_topic`이 `welfare_id`를 우선 인자로 받아 해석한다.
```python
async def get_active_topic(db, region="default", welfare_id=None):
    # 1순위: 담당 복지사의 이번 주 주제
    if welfare_id:
        result = await db.execute(
            select(WeeklyTopic).where(
                WeeklyTopic.active_week == monday,
                WeeklyTopic.welfare_id == welfare_id,
            ).order_by(WeeklyTopic.is_customized.desc()).limit(1)  # ← scalar_one_or_none 대신 limit(1)
        )
        topic = result.scalars().first()
        if topic:
            return _serialize(topic)
    # 2순위: 중앙 기본 주제(welfare_id IS NULL, region="default") — 선택적 유지
    # 3순위: 없음 → None (4-1)
```
`chat.py:81` 호출부도 `get_active_topic(db, region=region, welfare_id=user.welfare_id)`로 변경.

**주의**: 다중 결과 가능 지점은 모두 `scalar_one_or_none()` → `.scalars().first()` (+`order_by`/`limit(1)`)로 교체.

### 4-1. get_active_topic 폴백 제거

**현재**:
```python
# DB 조회 실패 → TOPIC_POOL 폴백
pool = (text_pool + image_pool) if (text_pool + image_pool) else TOPIC_POOL
idx = monday.isocalendar().week % len(pool)
topic = pool[idx].copy()
topic["id"] = None
return topic
```

**수정**:
```python
# DB 조회 실패 → None 반환
return None
```

**영향**: 폴백 제거의 파급은 `user.html`에만 국한되지 않는다. `chat.py:81`도 `get_active_topic()`을 호출하며, `topic=None`인 채 `claude.stream_chat(user.user_type, topic, ...)` (`chat.py:143`)에 그대로 전달된다.
- 4-5: `user.html`에 "이번 주 설문이 준비되지 않았습니다" 메시지 표시
- 4-4b: `stream_chat`이 `topic=None`을 안전하게 처리하는지 확인 후 방어 코드 추가 (주제 없이도 일반 대화 가능하도록)

### 4-2. save_weekly_topic에 welfare_id 포함

**현재**:
```python
existing = await db.execute(
    select(WeeklyTopic).where(
        WeeklyTopic.active_week == monday,
        WeeklyTopic.region == topic_data.get("region", "default"),
    )
)
```

**수정**:
```python
existing = await db.execute(
    select(WeeklyTopic).where(
        WeeklyTopic.active_week == monday,
        WeeklyTopic.region == topic_data.get("region", "default"),
        WeeklyTopic.welfare_id == topic_data.get("welfare_id"),
    )
)
```

**참고**: `welfare_id` 값 자체는 이미 `save_weekly_topic`(`public_data.py:1254`)에서 저장된다. 결함은 **upsert WHERE 절에서만 무시**된다는 점. 위 수정은 WHERE 절에 `welfare_id`를 추가하는 것.

**스케줄러/기본 주제(`welfare_id IS NULL`) 처리 결정**: 스케줄러 발행 주제는 `welfare_id=None`, `region="default"`로 저장한다. upsert WHERE에서 `welfare_id == None` 분기를 명시적으로 처리(`WeeklyTopic.welfare_id.is_(None)`)하여 복지사 주제와 충돌하지 않게 한다.

### 4-3. 복지사 API welfare_id 필터 추가

**`GET /surveys/current`**:
```python
@router.get("/surveys/current")
async def get_current_survey(
    welfare_id: str,  # ← 필수 파라미터 추가
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(WeeklyTopic).where(
            WeeklyTopic.active_week == monday,
            WeeklyTopic.welfare_id == uuid.UUID(welfare_id),  # ← 필터
        )
    )
```

**`GET /surveys/history`**: 동일하게 `welfare_id` 파라미터 추가.

**`GET /surveys/{topic_id}/analytics`** (`welfare.py:1015`): 시그니처를 `get_survey_analytics(topic_id: str, welfare_id: str, db=...)`로 변경하고, topic 조회 후 `topic.welfare_id == uuid.UUID(welfare_id)` 불일치 시 403 반환.

**`GET /surveys/current`·`/surveys/history` 동작 변경 주의**: 기존엔 region 무관 전체 주제를 반환했으나, `welfare_id` 필터 추가 후 복지사는 자기 주제만 보게 된다. 의도된 격리 동작임(시나리오 3과 일치).

### 4-4. 설문 응답 topic_id 검증

**현재**:
```python
if body.question_id and topic_uuid:
    survey_resp = SurveyResponse(...)
    db.add(survey_resp)
```

**수정**: `topic_uuid`가 `None`이면 400 Bad Request 반환.

```python
if body.question_id and topic_uuid:
    survey_resp = SurveyResponse(...)
    db.add(survey_resp)
elif body.question_id and not topic_uuid:
    raise HTTPException(status_code=400, detail="유효한 주제 ID가 없습니다. 먼저 주제를 발행해 주세요.")
```

### 4-5. 사용자 페이지: 주제 없음 처리

`user.html`에서 `get_active_topic()` 호출 결과가 `None`이면:
```html
<div class="empty-state">
  <p>이번 주 설문 주제가 아직 준비되지 않았습니다.</p>
  <p>담당 복지사가 주제를 발행하면 여기에 표시됩니다.</p>
</div>
```

---

## 5. 구현 순서

> 모든 경로는 저장소 루트 기준 `ium/backend/app/...` 이다 (계획 본문의 `backend/app/`는 `ium/` 접두 생략 표기).

```
Step 0: P0-0 get_active_topic welfare_id 우선 해석 ─→ public_data.py + chat.py  (선행: 1·2와 같이)
Step 1: P0-1 get_active_topic 폴백 완전 제거 ──────→ public_data.py
Step 2: P0-2 save_weekly_topic welfare_id 반영 ───→ public_data.py
Step 3: P0-3 복지사 API welfare_id 필터 추가 ─────→ welfare.py
Step 4: P0-4 설문 응답 topic_id 검증 ─────────────→ chat.py
Step 4b: P0-4b stream_chat None 방어 ─────────────→ chat.py + claude.py
Step 5: P1-1 사용자 페이지 주제 없음 메시지 ───────→ user.html
Step 6: 통합 테스트 (시나리오 1~4) ────────────────→
```

> **주의**: Step 0·1·2는 상호 의존적이다(다중 주제 허용 시 `scalar_one_or_none` 예외 회피를 Step 0이 담당). 반드시 함께 적용·검증한다.

---

## 6. 파일 목록

| 파일 | 작업 | 설명 |
|------|------|------|
| `ium/backend/app/services/public_data.py` | 수정 | P0-0, P0-1, P0-2 |
| `ium/backend/app/routers/welfare.py` | 수정 | P0-3 |
| `ium/backend/app/routers/chat.py` | 수정 | P0-0, P0-4, P0-4b |
| `ium/backend/app/services/claude.py` | 수정 | P0-4b (stream_chat None 방어) |
| `ium/backend/app/static/user.html` | 수정 | P1-1 |

---

## 7. 테스트 계획

### 시나리오 1: 정상 흐름
1. 복지사가 주제 발행 (welfare_id 포함)
2. 사용자가 로그인 → 해당 주제가 표시됨
3. 사용자가 설문 응답 제출
4. 복지사 대시보드 → 설문 통계에 응답 결과 표시
5. 제목 일치 확인

### 시나리오 2: 주제 없음
1. 주제가 발행되지 않은 상태에서 사용자 로그인
2. "이번 주 설문이 준비되지 않았습니다" 메시지 확인

### 시나리오 3: 복지사 격리 (같은 지역 포함 — 핵심)
1. **같은 region**의 복지사 A·B가 각각 주제 발행
2. A의 대시보드엔 A 주제만, B의 대시보드엔 B 주제만 표시
3. A 담당 사용자는 A 주제를, B 담당 사용자는 B 주제를 받음 (region 동일해도 welfare_id로 분기 — P0-0 검증)
4. 사용자 채팅 API가 `MultipleResultsFound` 없이 정상 응답 (scalar_one_or_none 제거 검증)
5. A가 `/surveys/{B의 topic}/analytics` 요청 시 403

### 시나리오 4: TOPIC_POOL 제거 검증
1. DB에 주제가 없는 상태에서 사용자 API 호출
2. `id=None`인 주제가 반환되지 않음 확인

---

## 8. 롤백 계획

모든 변경사항이 `main.py`를 제외한 서비스/라우터 로직이므로, 각 파일별로 Git revert 가능:

| 파일 | 롤백 방법 |
|------|-----------|
| `public_data.py` | `git checkout HEAD -- ium/backend/app/services/public_data.py` |
| `claude.py` | `git checkout HEAD -- ium/backend/app/services/claude.py` |
| `welfare.py` | `git checkout HEAD -- ium/backend/app/routers/welfare.py` |
| `chat.py` | `git checkout HEAD -- ium/backend/app/routers/chat.py` |
| `user.html` | `git checkout HEAD -- ium/backend/app/static/user.html` |

> **롤백 주의**: P0-0/1/2는 상호 의존적이므로 부분 롤백 시 `public_data.py`와 `chat.py`를 함께 되돌려야 정합성이 유지된다.

---

> **계획 승인 시 "수행"이라고 말해 주세요.**
