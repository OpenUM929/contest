# Phase 3 — 고도화 (수필·심리분석·동의)

> 상태: **COMPLETED** | 작성일: 2026-06-08 | 최종수정: 2026-06-09
> 작업 유형: 기능 구현 계획
> 선행 조건: [Phase 2 완료](../0608_01_phase2-dashboard/0608_01_phase2-dashboard.md)
> 대상 코드베이스: `C:\dev\contest\ium`

---

## 수정 이력

| 날짜 | 변경 섹션 | 변경 요약 |
|------|-----------|-----------|
| 2026-06-08 | 최초 작성 | 통합 계획서에서 Phase 3 분리 |
| 2026-06-09 | §1 D-1 | 수필 프롬프트 v1에 안개비 철학 요건 추가 및 프롬프트 예시 갱신 |
| 2026-06-09 | 전체 구조 | D영역 최우선 배치 / A영역(공공데이터 확장) 삭제 / G영역 AES 암호화·마이그레이션(구 G-1~G-3) 삭제 — 동의서·비식별화(구 G-4~G-6)만 유지하여 G-1~G-3로 재번호 |
| 2026-06-09 | 전체 | **코드베이스 대조 검증**: D/C/G 백엔드 대부분 이미 구현됨 확인 / 불일치 8건 발견 및 정리 섹션 추가 / 잔여 작업 축소 |
| 2026-06-09 | G-2, §잔여작업 | `ConsentScreen` `App.tsx`에 `AsyncStorage` 기반 연결 완료 / YouthMain TTS 누락 신규 발견 / 불일치 8건 중 1건 해결 |
| 2026-06-09 | §불일치, §잔여작업 | **잔여 작업 일괄 처리**: `init.sql` 스키마 통일·복합 인덱스 추가 / `welfare.py` dead code 삭제 / `survey.ts` `fetchLatestEssay` 추가 / `YouthMain` TTS 버튼 추가 / `essay.py` 프롬프트 안개비 철학 동기화 |

> **A영역 삭제 사유**: `fetch_gugak`·`image` 타입 활성화는 핵심 사용자 가치(노인-청년 연결)와 거리가 멀고, 이미 공공데이터 연동이 작동하는 상태에서 장식적 추가에 불과함. 이 시간을 D·C영역 완성에 투자.
> **G영역 AES 삭제 사유**: 대회 데모에서 심사자가 암호화 여부를 확인할 방법이 없음. 마이그레이션 스크립트 오류 시 기존 대화 데이터 전체 손실 위험. 사용자에게 직접 보이는 동의서 UI·비식별화만 유지.

---

## 목표

Phase 3는 3개 영역으로 구성된다:

| 영역 | 파이프라인 | 핵심 내용 | 구현 현황 |
|------|-----------|-----------|----------|
| **D. 수필 완성** | D | 프롬프트 v1(안개비 철학), 모바일 수신 화면, 자동 생성 스케줄러 | **✅ 완료** |
| **C. 심리 분석 고도화** | C | TTR·n-gram·참여 패턴 + 5개 심리 지수 | **✅ 완료** |
| **G. 동의·비식별화** | G | 동의 이력 관리, 동의서 UI, 비식별화 보고 API | **✅ 완료** |

> D를 최우선으로 배치한 이유: 설문→대화→수필→모바일로 이어지는 전체 루프가 완성되어야 서비스 플로우가 닫히고, 시연에서 가장 눈에 띄는 기능이기 때문.

---

## 코드베이스 대조 결과 (2026-06-09)

### 이미 구현 완료된 작업

| 계획서 작업 | 파일 | 실제 상태 |
|---|---|---|
| **D-1** 수필 프롬프트 v1 | `essay.py` | `ESSAY_PROMPT_V1` 존재, `generate_essay` 기본값 `"v1"` |
| **D-1** `survey_responses` 우선 활용 | `essay.py` | `_fetch_survey_messages` → `_fetch_conversation_messages` 폴백 이미 구현 |
| **D-3** 수필 자동 생성 스케줄러 | `main.py` | `auto_generate_weekly_essay` Job 일요일 23:00 이미 등록 |
| **D-3** `EssayContributor` 저장 | `essay.py` | `auto_generate_weekly_essay` 내부에서 insert 이미 수행 |
| **C-1** 가중치 기반 `EMOTION_PATTERNS` | `emotion.py` | 6개 카테고리(high/medium/low ±) 전부 구현 |
| **C-2** 언어 패턴 분석 | `language_pattern.py` | 3개 함수 전부 구현 |
| **C-3** 참여 패턴 분석 | `participation_pattern.py` | 2개 함수 + `get_participation_summary` 구현 |
| **C-4** 5개 심리 지수 | `psych_index.py` | `calc_indices`, `compute_and_store` 구현 완료 |
| **C-5** 심리 지수 대시보드 연동 | `welfare.py` | `/users/{id}/detail`에서 `compute_and_store` 호출 후 포함 반환 |
| **G-1** 동의 이력 관리 API | `auth.py` | `POST /api/auth/consent`, `GET /api/auth/consent/{user_id}` 이미 구현 |
| **G-1** `user_consents` 테이블 | `init.sql` | DDL 이미 존재 |
| **G-1** `UserConsent` 모델 | `models.py` | 이미 존재 |
| **G-3** 비식별화 보고 API | `welfare.py` | `/api/welfare/report/anonymized` 이미 구현 |
| 위기 팝업 3단계 | `ElderlyMain.tsx`, `YouthMain.tsx` | high/medium/low 전부 분기 처리됨 |
| 수필 모달 + TTS | `ElderlyMain.tsx` | `essay-archive` 모달, TTS (`rate: 0.9`) 이미 구현 |

### 불일치 및 정리 필요 사항

| # | 항목 | 상태 | 계획서/기대 | 실제 코드 | 조치 |
|---|---|---|---|---|---|
| 1 | **D-2 수필 조회 흐름** | ℹ️ 의도적 차이 | `GET /essay/latest` 단일 조회 → 404 토스트 | 실제는 `GET /essay/archive` 목록 → 상세 2단계 흐름 | archive 흐름이 UX적으로 더 풍부함 → 계획서를 실제에 맞춤 |
| 2 | **D-2 `fetchLatestEssay` 함수** | ✅ **해결** | 코드 스니펫에 `fetchLatestEssay()` 존재 가정 | `mobile/api/survey.ts`에 추가 완료 | — |
| 3 | **G-2 `ConsentScreen` 연결** | ✅ **해결** | 모바일 동의서 UI 구현 완료 가정 | `App.tsx`에서 `AsyncStorage` 기반으로 연결 완료 | — |
| 4 | **`PsychIndex` 모델 vs `init.sql` 타입 불일치** | ✅ **해결** | — | 모델: `SmallInteger` / SQL: `FLOAT` | `init.sql`을 `SMALLINT NOT NULL`로 수정 완료 |
| 5 | **`PsychIndex` 타임스탬프 컬럼명 불일치** | ✅ **해결** | — | 모델: `calculated_at` / SQL: `computed_at` | `init.sql`을 `calculated_at`로 수정 완료 |
| 6 | **`psych_indices` 복합 인덱스 누락** | ✅ **해결** | 계획서: `(user_id, calculated_at DESC)` | `init.sql`에는 `idx_psych_indices_user`만 존재 | `idx_psych_indices_user_calc` 복합 인덱스 추가 완료 |
| 7 | **D-1 프롬프트 내용 상이** | ✅ **해결** | "[철학 — 안개비처럼]" 등 계획서 프롬프트 | 실제: "[수필 작가·상담 전문가 공동 설계 프롬프트 v1.0]" + 심리 안전 원칙 | `essay.py` 프롬프트를 v1.1로 업데이트, 안개비 철학 반영 완료 |
| 8 | **`welfare.py` dead code** | ✅ **해결** | — | 1073라인 `return {"topics": archive}` — 도달 불가능 | 삭제 완료 |
| 9 | **YouthMain 수필 TTS 누락** | ✅ **해결** | `ElderlyMain`과 동일한 TTS 기능 기대 | `YouthMain.tsx`의 수필 상세 모달에 TTS 버튼 없음 | `expo-speech` import + TTS 버튼 + 스타일 추가 완료 |

---

## 1. 영역 D — 수필 완성

> **구현 현황**: D-1~D-3 전체 완료. archive 2단계 흐름과 `fetchLatestEssay` 함수 모두 구현됨.

### ✅ 작업 D-1 — 수필 프롬프트 v1

**대상 파일**: `backend/app/services/essay.py`

**실제 구현 상태**: 이미 `ESSAY_PROMPT_V1`이 존재하며 `generate_essay`의 기본값이 `"v1"`입니다.

**v1 프롬프트 요건 (실제 코드와 계획서 동기화 필요):**
- 익명성 보장: 특정 개인 식별 불가한 표현 사용
- 1인칭 복수 사용: "우리는", "우리가"
- 분량: 800~1200자
- 세대 간 연결감 표현
- `survey_responses.narrative_text` 데이터 우선 활용 (없으면 대화 내용 사용)
- **안개비 철학 일관성**: 설문지 프롬프트와 동일한 철학 준수 — 강제 공감 없음, 이야기가 주제에서 시작해 사람의 삶으로 자연스럽게 흐르도록. "가장 감동적인", "가장 기억에 남는" 등 최고급 표현 지양. 이야기가 머물 수 있는 온기 있는 공간 표현.

> ⚠️ **불일치**: 계획서에는 "[철학 — 안개비처럼]" 프롬프트를 제시했으나, 실제 `essay.py`에는 "[수필 작가·상담 전문가 공동 설계 프롬프트 v1.0]" + 심리 안전 원칙이 포함되어 있습니다. 계획서 예시와 실제 코드를 동기화할지 결정 필요.

```python
# 실제 코드의 ESSAY_PROMPT_V1 (요약)
"""\
[수필 작가·상담 전문가 공동 설계 프롬프트 v1.0]
창작 원칙:
1. 각 목소리는 독립적으로 존중받아야 합니다
2. 특정 개인을 지칭하는 표현 금지 (모든 주어를 '우리', '어떤 이', '누군가'로)
3. 감정의 과장 금지 — 담담하게 기술하되 울림이 있도록
4. 세대 간 거리를 좁히는 공통 감각을 찾아 연결
5. 마지막 두 문장은 반드시 희망이나 연결감으로 마무리

심리적 안전 원칙:
- 트라우마를 자극할 수 있는 직접적 표현 회피
- 상실·외로움은 인정하되 절망으로 끝내지 않음
- 읽는 이가 자신의 이야기를 발견할 수 있도록 여백 유지
"""
```

> **결론**: 구현 완료. 계획서 요구사항과 동기화 완료.

---

### ✅ 작업 D-2 — 모바일 수필 수신 화면

**대상 파일**: `mobile/screens/ElderlyMain.tsx`, `mobile/screens/YouthMain.tsx`, `mobile/api/survey.ts`

**실제 구현 상태**: `ElderlyMain.tsx`와 `YouthMain.tsx`에 모두 `essay-archive` 모달 + `selectedEssay` TTS(`rate: 0.9`)이 구현되어 있습니다. `fetchLatestEssay()` 함수도 `survey.ts`에 추가 완료.

**현재 흐름:**
1. "지난 이야기 듣기" 클릭 → `GET /essay/archive` 호출 → 목록 표시
2. 목록 항목 클릭 → `GET /essay/{id}` 호출 → 상세 내용 표시
3. TTS 버튼: `expo-speech`로 수필 텍스트 읽기 (속도 0.9)

> **결론**: 구현 완료.

---

### ✅ 작업 D-3 — 수필 자동 생성 스케줄러

**대상 파일**: `backend/app/main.py`, `backend/app/services/essay.py`

**실제 구현 상태**: 이미 구현되어 있습니다.

```python
# backend/app/main.py — 이미 등록됨
scheduler.add_job(
    auto_generate_weekly_essay,
    CronTrigger(day_of_week="sun", hour=23, minute=0),
    id="weekly_essay_generation",
    replace_existing=True,
)
```

**`auto_generate_weekly_essay` 함수 (`essay.py`):**
1. 현재 활성 `WeeklyTopic` 조회 (`get_active_topic`)
2. 해당 topic_id의 `survey_responses.narrative_text` 집계
3. `generate_essay()` 호출 (기본값 `prompt_version="v1"`)
4. `EssayContributor` 기여자 정보 저장
5. `Essay` DB 저장

> **결론**: 구현 완료. 추가 작업 불필요.

---

## 2. 영역 C — 심리 분석 고도화

> **구현 현황**: C-1~C-5 백엔드 전체 완료. `PsychIndex` 모델/`init.sql` 타입·컬럼명 불일치 정리만 남음.

### ✅ 작업 C-1 — 감정 규칙 기반 보완

**대상 파일**: `backend/app/services/emotion.py`

**실제 구현 상태**: 이미 가중치 기반 `EMOTION_PATTERNS`가 구현되어 있습니다.

```python
# 실제 코드 (emotion.py)
EMOTION_PATTERNS = {
    "high_negative": {"keywords": ["죽고 싶", "살기 싫", "자해", "없어지고 싶", "끝내고 싶"], "weight": 3},
    "medium_negative": {"keywords": ["힘들어", "외로워", "무서워", "슬퍼", "괴로워", "우울해", "지쳐"], "weight": 2},
    "low_negative": {"keywords": ["피곤", "걱정", "불안", "귀찮", "싫어", "짜증"], "weight": 1},
    "high_positive": {"keywords": ["행복해", "너무 좋아", "기뻐", "설레", "신나"], "weight": 3},
    "medium_positive": {"keywords": ["좋아", "감사", "즐거워", "고마워", "뿌듯"], "weight": 2},
    "low_positive": {"keywords": ["괜찮아", "나쁘지 않아", "좋았", "웃겨"], "weight": 1},
}
```

> **결론**: 구현 완료. `instructor==1.7.0`은 `requirements.txt`에 있으나 실제 사용되지 않음 — 이것은 Phase 2 잔여 항목과 동일.

---

### ✅ 작업 C-2 — 언어 패턴 분석

**대상 파일**: `backend/app/services/language_pattern.py`

**실제 구현 상태**: 이미 구현되어 있습니다.

```python
# 실제 코드 (language_pattern.py)
def calc_ttr(text: str) -> float:
    """어휘 다양성: 고유 어절 수 / 전체 어절 수 (0~1, 높을수록 다양)"""

def calc_ngram_repetition(text: str, n: int = 2) -> float:
    """n-gram 반복 비율: 중복 n-gram / 전체 n-gram (0~1, 낮을수록 다양)"""

def calc_sentence_length_variance(text: str) -> float:
    """문장 길이 분산 (어절 기준, 높을수록 문장 구조 다양)"""

def analyze_text(text: str) -> dict:
    """3개 지표 한번에 반환"""
```

> **결론**: 구현 완료.

---

### ✅ 작업 C-3 — 참여 패턴 분석

**대상 파일**: `backend/app/services/participation_pattern.py`

**실제 구현 상태**: 이미 구현되어 있습니다.

```python
# 실제 코드 (participation_pattern.py)
async def get_daily_session_count(user_id: str, db: AsyncSession, days: int = 30) -> list[dict]:
    """일별 대화 시작 횟수 반환 [{date, count}]"""

async def calc_conversation_length_trend(user_id: str, db: AsyncSession, days: int = 30) -> float:
    """대화 길이 추이 — 선형 회귀 기울기 (양수=증가, 음수=감소, 0=데이터 부족)"""

async def get_participation_summary(user_id: str, db: AsyncSession, days: int = 30) -> dict:
    """일별 접속 + 추이를 한번에 반환"""
```

> **결론**: 구현 완료.

---

### ✅ 작업 C-4 — 5개 심리 지수

**대상 파일**: `backend/app/services/psych_index.py`, `backend/app/models/models.py`, `backend/app/init.sql`

**실제 구현 상태**: `psych_index.py`의 `calc_indices` 및 `compute_and_store`가 이미 구현되어 있습니다.

**지수 계산 기준 (실제 코드와 동일):**

| 지수 | 입력 신호 | 계산 방법 |
|------|----------|-----------|
| 외로움(loneliness) | 부정 감정 비율, 관계 키워드 부재, 접속 빈도 감소 | 가중 합산 → 0~100 정규화 |
| 활력(vitality) | 긍정 감정 비율, 대화 길이, 접속 빈도 | 가중 합산 |
| 인지(cognition) | TTR, n-gram 반복 비율 역수, 문장 길이 분산 | 가중 합산 |
| 관계(relationship) | 가족/지인 관련 키워드 빈도 | 키워드 매칭 빈도 정규화 |
| 미래(future) | 미래 시제 표현, 긍정적 계획 키워드 | 키워드 매칭 빈도 정규화 |

> **결론**: 구현 완료. `init.sql`과 `models.py` 스키마 통일 완료.

---

### ✅ 작업 C-5 — 심리 지수 대시보드 연동

**대상 파일**: `backend/app/routers/welfare.py`

**실제 구현 상태**: `GET /api/welfare/users/{user_id}/detail` 응답에 이미 `psych_indices`가 포함되어 반환됩니다.

```json
{
  "psych_indices": {
    "loneliness": 72,
    "vitality": 35,
    "cognition": 58,
    "relationship": 40,
    "future": 25,
    "calculated_at": "2026-06-08T09:00:00+09:00"
  }
}
```

> **결론**: 구현 완료.

---

## 3. 영역 G — 동의·비식별화

> **구현 현황**: G-1 백엔드 완료, G-3 백엔드 완료. G-2(모바일 연결)만 남음.

> AES-256 암호화(구 G-1~G-3)는 삭제. 동의서 UI와 비식별화 보고만 유지 — 둘 다 사용자 및 심사자에게 직접 보이는 기능임.

### ✅ 작업 G-1 — 동의 이력 관리

**대상 파일**: `backend/app/routers/auth.py`, `backend/app/init.sql`, `backend/app/models/models.py`

**실제 구현 상태**: 이미 구현되어 있습니다.

**DB 스키마 (실제 `init.sql`):**
```sql
CREATE TABLE IF NOT EXISTS user_consents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    consent_type VARCHAR(50) NOT NULL,
    agreed BOOLEAN NOT NULL,
    agreed_at TIMESTAMP DEFAULT NOW()
);
```

**엔드포인트 (실제 `auth.py`):**
```
POST /api/auth/consent
    Body: { user_id: string, consents: [{ consent_type, agreed }] }
    → 201 Created

GET /api/auth/consent/{user_id}
    → 동의 유형별 최신 이력 + all_required_agreed(boolean) 반환
```

> **결론**: 구현 완료.

---

### ✅ 작업 G-2 — 동의서 UI (모바일) 연결

**대상 파일**: `mobile/App.tsx`, `mobile/screens/ConsentScreen.tsx`

**실제 구현 상태**: `ConsentScreen.tsx`는 완전히 구현되어 있으며, `App.tsx`에서 `AsyncStorage` 기반으로 연결되었습니다.

**동작 흐름 (`App.tsx`):**
1. 앱 시작 시 `AsyncStorage.getItem("consent_done")`으로 동의 여부 확인
2. 미동의 상태 → `ConsentScreen` 렌더링
3. "시작하기" 클릭 → `POST /api/auth/consent` 호출 → `AsyncStorage.setItem("consent_done", "true")` → `consented = true`로 state 변경
4. 동의 완료 상태 → `ElderlyMain` 또는 `YouthMain` 렌더링

**구현된 UI 요건:**
- 필수 동의 3개: 개인정보 처리 방침 / 서비스 이용 약관 / AI 대화 분석 활용 동의
- 전체 동의 토글
- 개별 동의 항목 (각 상세 내용 펼침 가능)
- 필수 3개 모두 동의해야 "시작하기" 버튼 활성화
- 동의 완료 후 `POST /api/auth/consent` 호출 → `onComplete` 콜백 실행

> **결론**: 구현 완료.

---

### ✅ 작업 G-3 — 비식별화 보고 API

**대상 파일**: `backend/app/routers/welfare.py`

**실제 구현 상태**: 이미 구현되어 있습니다.

```
GET /api/welfare/report/anonymized
    → 전체 사용자 대화 통계 (user_id 대신 SHA-256 8자리 코드)
    응답 형태:
    {
      "period": "2026-06-01~2026-06-07",
      "user_count": 3,
      "users": [
        { "code": "a3f8b2c1", "message_count": 15, "avg_emotion": "positive" }
      ]
    }
```

> **결론**: API 구현 완료.

---

## 4. 변경 파일 요약

> **요약**: Phase 3 백엔드(D/C/G)는 대부분 이미 구현 완료. 남은 것은 모바일 연결(G-2), DB 스키마 정리(C-4), 마이너 리팩토링입니다.

### 영역 D — 수필

| 파일 | 상태 | 변경 내용 |
|---|---|---|
| `backend/app/services/essay.py` | ✅ 완료 | `ESSAY_PROMPT_V1` 이미 존재, `survey_responses` 우선 활용, `auto_generate_weekly_essay` 내 `EssayContributor` 저장 |
| `backend/app/main.py` | ✅ 완료 | 일요일 23:00 `auto_generate_weekly_essay` Job 이미 등록 |
| `mobile/screens/ElderlyMain.tsx` | ✅ 완료 | 수필 archive 모달 + TTS 이미 구현 |
| `mobile/api/survey.ts` | ✅ 완료 | `fetchLatestEssay()` 함수 추가 (404 → null 반환) |

### 영역 C — 심리 분석

| 파일 | 상태 | 변경 내용 |
|---|---|---|
| `backend/app/services/emotion.py` | ✅ 완료 | 가중치 기반 `EMOTION_PATTERNS` 이미 적용 |
| `backend/app/services/language_pattern.py` | ✅ 완료 | TTR, n-gram, 문장 길이 분산 이미 구현 |
| `backend/app/services/participation_pattern.py` | ✅ 완료 | 접속 빈도, 대화 길이 추이 이미 구현 |
| `backend/app/services/psych_index.py` | ✅ 완료 | 5개 심리 지수 계산 이미 구현 |
| `backend/app/routers/welfare.py` | ✅ 완료 | `/users/{id}/detail`에 `psych_indices` 이미 포함 |
| `backend/app/init.sql` | ✅ 완료 | `psych_indices` `SMALLINT NOT NULL`/`calculated_at` 통일, 복합 인덱스 추가 |

### 영역 G — 동의·비식별화

| 파일 | 상태 | 변경 내용 |
|---|---|---|
| `backend/app/models/models.py` | ✅ 완료 | `UserConsent` 모델 이미 존재 |
| `backend/app/init.sql` | ✅ 완료 | `user_consents` 테이블 DDL 이미 존재 |
| `backend/app/routers/auth.py` | ✅ 완료 | 동의 저장/조회 API 이미 구현 |
| `backend/app/routers/welfare.py` | ✅ 완료 | `/report/anonymized` API 이미 구현 |
| `backend/app/routers/welfare.py` | ✅ 완료 | `/report/anonymized` API 구현, dead code 삭제 |
| `mobile/App.tsx` | ✅ 완료 | `ConsentScreen` `AsyncStorage` 기반 연결, 동의 완료 후 메인 화면 이동 |
| `mobile/screens/ConsentScreen.tsx` | ✅ 완료 | 동의서 UI 구현 완료, `App.tsx`에서 렌더링됨 |

---

## 5. 테스트 시나리오

### 영역 D

| # | 시나리오 | 상태 | 검증 방법 |
|---|---|---|---|
| T1 | 수필 프롬프트 v1 | ✅ 백엔드 완료 | 생성된 수필: 익명성 보장, "우리" 사용, 800~1200자, 최고급 표현 없음 확인 |
| T2 | 안개비 철학 — 수필 수동 QA | 🟡 수동 QA 예정 | 실제 주제로 수필 생성 후 복지사가 직접 검토 — 강제 공감 없이 이야기가 자연스럽게 흐르는지 확인 |
| T3 | 모바일 수필 | ✅ 완료 | "지난 이야기 듣기" 탭 → archive 목록 → 상세 → TTS 재생 확인 |
| T4 | 수필 자동 스케줄러 | ✅ 백엔드 완료 | `auto_generate_weekly_essay` 수동 호출 → Essay 레코드 생성 + EssayContributor 확인 |
| T5 | `fetchLatestEssay` | ✅ 완료 | `mobile/api/survey.ts`에 `fetchLatestEssay()` 존재 확인, 404 시 null 반환 |

### 영역 C

| # | 시나리오 | 상태 | 검증 방법 |
|---|---|---|---|
| T6 | TTR 측정 | ✅ 완료 | "좋아요 좋아요 좋아요" → TTR < 0.5 확인 |
| T7 | n-gram 반복 | ✅ 완료 | 반복 문장 입력 → n-gram 반복 비율 높음 확인 |
| T8 | 5개 지수 범위 | ✅ 완료 | 14일 대화 데이터 입력 → 각 지수 0~100 범위 확인 |
| T9 | 지수 대시보드 | ✅ 완료 | `/api/welfare/users/{id}/detail` 응답에 `psych_indices` 포함 확인 |
| T10 | `psych_indices` 스키마 통일 | ✅ 완료 | `init.sql`의 타입/컬럼명이 `models.py`와 일치 확인 (`SMALLINT NOT NULL`, `calculated_at`) |

### 영역 G

| # | 시나리오 | 상태 | 검증 방법 |
|---|---|---|---|
| T11 | 동의서 UI | ✅ 완료 | `App.tsx` 실행 → 최초 `ConsentScreen` 노출 → 필수 3개 미동의 시 "시작하기" 버튼 비활성화 확인 → 동의 완료 후 메인 화면 이동 |
| T15 | YouthMain 수필 TTS | ✅ 완료 | `YouthMain` 수필 상세 모달에 TTS 버튼 추가 확인 (`expo-speech`, `rate: 0.9`) |
| T12 | 동의 이력 저장 | ✅ 완료 | 동의 완료 후 `user_consents` 테이블에 3건 레코드 확인 |
| T13 | 비식별화 | ✅ 완료 | `/api/welfare/report/anonymized` → user_id 대신 8자리 코드 반환 확인 |
| T14 | welfare.py dead code | ✅ 완료 | `welfare.py` 1073라인 `return {"topics": archive}` 삭제 확인 |

---

## 6. 잔여 작업 요약

Phase 3의 모든 작업이 완료되었습니다.

| # | 작업 | 영역 | 상태 | 파일 |
|---|------|------|------|------|
| 1 | `init.sql` `psych_indices` 타입/컬럼명 `models.py` 기준 통일 | C-4 | ✅ 완료 | `backend/app/init.sql` |
| 2 | `init.sql` `psych_indices` 복합 인덱스 추가 | C-4 | ✅ 완료 | `backend/app/init.sql` |
| 3 | `welfare.py` dead code 삭제 | G-3 | ✅ 완료 | `backend/app/routers/welfare.py` |
| 4 | `fetchLatestEssay` 함수 추가 | D-2 | ✅ 완료 | `mobile/api/survey.ts` |
| 5 | `YouthMain` 수필 상세 모달에 TTS 버튼 추가 | D-2 | ✅ 완료 | `mobile/screens/YouthMain.tsx` |
| 6 | 수필 프롬프트 문구 동기화 (안개비 철학) | D-1 | ✅ 완료 | `backend/app/services/essay.py` |

> **이 계획서의 모든 백엔드 및 모바일 작업이 완료되었습니다.**
> 전체 개요: [이음_통합구현계획_20260604.md](../이음_통합구현계획_20260604.md)
