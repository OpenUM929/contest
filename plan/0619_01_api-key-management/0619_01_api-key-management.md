# 복지사 API 키 관리 + AI 제공자 선택 시스템 설계 계획서

> 상태: DONE (구현 완료) | 작성일: 2026-06-19 | 작업 유형: 신규 기능 개발

---

## 수정 이력

| 날짜 | 변경 섹션 | 변경 요약 |
|------|-----------|-----------|
| 2026-06-19 | 최초 작성 | — |
| 2026-06-20 | 전체 / 2-1 / 2-3 / 2-5 / 2-8 / 6 / 8 | 검토 반영: ① 파일 경로 `ium/` 기준 정정 ② 키 1개 시 `active_provider` 자동 설정 규칙 추가 ③ API 키 엔드포인트 접근 제어 추가 ④ Gemini 모델 현행화 ⑤ `openai` 의존성 추가 ⑥ 암호화 키 저장 한계 명시 ⑦ 저장 동시성(파일 락) 처리 ⑧ essay welfare_id 출처 정리 |
| 2026-06-20 | 구현 | 전체 구현 완료. 신규 4파일 + 수정 9파일. PUT 빈 키 = "변경 없음(유지)"로 구현(마스킹 키 재전송 불가 대응). `cryptography` 설치, 암호화 roundtrip·단일키 자동활성 스모크 테스트 통과. `.gitignore`에 키 파일 등록. |

---

## 1. 개요

이음(以音) 프로젝트에서 **복지사(WelfareWorker)가 자신의 AI API 키를 등록**하고, 등록된 키를 **주간 주제 선정·질문 생성·작품 생성 등 AI 호출 전반에 사용**할 수 있도록 합니다.

### 1-1. 목표

- 복지사가 대시보드에서 Claude / GPT / Gemini API 키를 직접 입력/저장
- 저장된 키는 서버에 **암호화**되어 파일로 보관
- **2개 이상**의 키가 등록된 경우 복지사가 라디오 버튼으로 **활성 제공자** 선택
- 선택한 AI 제공자가 **주제 질문 생성, 질문 수정, 유물 분석, 작품 생성**에 적용됨
- API 키가 없으면 **기존 시스템 설정**(OpenCode / Claude)으로 fallback

### 1-2. 적용 범위

| # | 기능 | 엔드포인트 | 현재 AI | 변경 후 |
|:-:|------|-----------|---------|---------|
| 1 | 주제 질문 생성 | `POST /api/welfare/topics/generate-questions` | OpenCode | 복지사 키 → 시스템 fallback |
| 2 | 주제 질문 수정 | `POST /api/welfare/topics/refine-questions` | OpenCode | 복지사 키 → 시스템 fallback |
| 3 | 유물 분석 | `POST /api/welfare/topics/analyze` | OpenCode | 복지사 키 → 시스템 fallback |
| 4 | 작품 생성 | `POST /api/essay/generate` | Claude → OpenCode | 복지사 키 → 시스템 fallback |

---

## 2. 백엔드 설계

### 2-1. 암호화 키 저장소 (`app/services/api_key_store.py`) — 신규

**파일 위치**: `ium/backend/data/api_keys.enc`

**암호화 방식**: Fernet (AES-256-CBC + HMAC, `cryptography` 라이브러리)

**암호화 키 관리** (우선순위):
1. 환경변수 `IUM_API_KEY_ENCRYPTION_KEY` (운영 환경) — **권장**
2. `ium/backend/.api_key_encryption_key` 파일 (개발 환경)
3. 최초 실행 시 자동 생성 → `.api_key_encryption_key` 파일 저장

> ⚠️ **보안 한계 명시**: 2·3번 방식은 암호화 키 파일(`.api_key_encryption_key`)이
> 암호문(`api_keys.enc`)과 **동일 디렉터리**에 저장되므로, 파일 시스템 접근이 뚫리면
> 둘 다 노출되어 사실상 평문과 같습니다. 운영 환경에서는 **반드시 1번(환경변수)** 을 사용하고,
> 키 파일은 `.gitignore`에 등록해 커밋되지 않도록 합니다.

**저장 데이터 구조** (복호화 후 JSON):
```json
{
  "b1c2d3e4-f5a6-4b7c-8d9e-0f1a2b3c4d5e": {
    "claude": "sk-ant-xxxxxxxxxxxx",
    "openai": "sk-xxxxxxxxxxxx",
    "gemini": "AIzaxxxxxxxxxxxx",
    "active_provider": "claude"
  },
  "c1d2e3f4-a5b6-4c7d-8e9f-0a1b2c3d4e5f": {
    "claude": "",
    "openai": "",
    "gemini": "",
    "active_provider": ""
  }
}
```

**주요 함수**:
| 함수 | 설명 |
|------|------|
| `_ensure_key() -> bytes` | 암호화 키 로드 또는 생성 |
| `_get_cipher() -> Fernet` | 암호화/복호화 객체 반환 |
| `_file_path() -> Path` | `api_keys.enc` 파일 경로 |
| `load_all() -> dict` | 파일 → 복호화 → 전체 dict 반환 (파일 없으면 빈 dict) |
| `save_all(data: dict)` | 전체 dict → 암호화 → 파일 저장 |
| `get_worker_keys(welfare_id: str) -> dict` | 특정 복지사 키 조회 (없으면 빈 dict) |
| `set_worker_keys(welfare_id: str, keys: dict)` | 특정 복지사 키 저장 (merge 방식) |

> **동시성 처리**: `set_worker_keys`는 `load_all → merge → save_all` 순서로 동작하므로,
> 동시 PUT 요청 시 갱신 유실(lost update)이 발생할 수 있습니다. `threading.Lock`(또는
> `filelock` 라이브러리)으로 읽기-쓰기 구간을 직렬화합니다. 규모상 충돌 가능성은 낮으나
> 데이터 손실을 막기 위해 락을 둡니다.

### 2-2. AI 제공자 통합 서비스 (`app/services/ai_provider.py`) — 신규

**제공자 감지 방식**: API 키 접두사 기반이 아닌 **명시적 provider 문자열** 사용
- 복지사가 라디오 버튼으로 선택한 `active_provider` 값을 그대로 사용

**통합 인터페이스**:
```python
async def call_ai(
    prompt: str,
    provider: str,         # "claude" | "openai" | "gemini"
    api_key: str,
    max_tokens: int = 1500,
    system_prompt: str | None = None,
) -> str | None:
```

**제공자별 구현**:

| 제공자 | 함수 | SDK/API | 모델 |
|--------|------|---------|------|
| Claude | `_call_claude()` | `anthropic.AsyncAnthropic` (기존 설치됨) | `claude-sonnet-4-6` |
| GPT | `_call_openai()` | httpx → REST API | `gpt-4o` |
| Gemini | `_call_gemini()` | httpx → REST API | `gemini-2.0-flash` |

> **SDK 의존성 통일**: OpenAI도 Gemini와 동일하게 **httpx로 REST API를 직접 호출**합니다.
> `openai` SDK를 추가 설치하지 않아도 되어 의존성이 단순해지고, 세 제공자의 에러 처리
> 로직을 한 곳에서 일관되게 다룰 수 있습니다. (Claude만 기존에 이미 설치된
> `anthropic` SDK를 재사용)
> `gemini-pro`는 레거시 모델이므로 현행 `gemini-2.0-flash`를 사용합니다.

**공통 에러 처리**:
- API 키 유효성 검증 (401/403 → `None` 반환)
- 타임아웃 (30초 → `None` 반환)
- rate limit (429 → 1회 재시도)
- 모든 실패 시 `None` 반환 (호출자가 fallback 처리)

### 2-3. API 키 CRUD 엔드포인트 (`app/routers/welfare.py`에 추가)

> 🔐 **접근 제어 (필수)**: API 키는 평문 자격증명이므로 `welfare_id`만으로 조회/수정하게
> 두면 안 됩니다(`welfare_id`만 알면 타인의 키를 덮어쓰거나 상태를 열람 가능). 두 엔드포인트
> 모두 **요청자의 인증 정보와 `welfare_id`가 일치하는지 검증**합니다. 현재 인증 체계에
> 토큰이 없다면 최소한 `WelfareWorker` 존재 여부 확인 + (가능 시) 로그인 세션의 본인
> `welfare_id` 일치 검사를 추가합니다.

#### GET `/api/welfare/api-keys?welfare_id={id}`

**응답** (키는 마스킹):
```json
{
  "claude": "****...abcd",
  "openai": "",
  "gemini": "****...wxyz",
  "active_provider": "gemini"
}
```

- 마스킹 규칙: 마지막 4자리만 보존, 앞은 `*` 처리. **키 길이가 8자 미만이면 전체를 `*`로 마스킹**(짧은 키 노출 방지)
- 빈 키는 빈 문자열 반환

#### PUT `/api/welfare/api-keys`

**요청 본문**:
```json
{
  "welfare_id": "b1c2d3e4-...",
  "claude": "sk-ant-xxxxxxxx",
  "openai": "",
  "gemini": "AIzaxxxxxxxx",
  "active_provider": "claude"
}
```

- **빈 문자열로 전송된 키는 "변경 없음"으로 보고 기존 값을 유지** (프론트는 마스킹된 키만
  보유하므로 기존 키를 재전송할 수 없음 → 활성 제공자만 바꿀 때 다른 키가 지워지는 사고 방지)
- `active_provider`는 항상 갱신하며, 빈 키를 가리키면 `active_provider`를 초기화
- **키 1개 자동 활성화**: 저장 후 비어있지 않은 키가 **정확히 1개**이면
  `active_provider`를 그 제공자로 자동 설정한다. (프론트가 라디오를 2개 이상일 때만
  노출하므로, 이 규칙이 없으면 키 1개만 등록한 복지사는 `active_provider`가 빈 값으로
  남아 키가 사용되지 않고 시스템 fallback으로 빠지는 버그가 발생함)
- 키가 0개이면 `active_provider`는 빈 문자열

### 2-4. 기존 Request 모델 수정

#### `GenerateQuestionsRequest` (welfare.py:724)
```python
class GenerateQuestionsRequest(BaseModel):
    welfare_id: str | None = None       # ← 추가
    title: str
    description: str | None = None
    ...
```

#### `RefineQuestionsRequest` (welfare.py:761)
```python
class RefineQuestionsRequest(BaseModel):
    welfare_id: str | None = None       # ← 추가
    topic_title: str
    current_question_set: dict
    instruction: str
```

#### `ArtifactAnalyzeRequest` (welfare.py:1406)
```python
class ArtifactAnalyzeRequest(BaseModel):
    welfare_id: str | None = None       # ← 추가
    title: str
    description: str = ""
    ...
```

#### API Key 설정 전용 Request — 신규
```python
class ApiKeysSaveRequest(BaseModel):
    welfare_id: str
    claude: str = ""
    openai: str = ""
    gemini: str = ""
    active_provider: str = ""
```

### 2-5. 기존 서비스 수정

#### `public_data.py:generate_topic_question()`

```python
async def generate_topic_question(
    ...,
    welfare_id: str | None = None,     # ← 추가
) -> tuple[QuestionSet, bool]:
```

로직:
1. `welfare_id`가 있으면 → `api_key_store.get_worker_keys(welfare_id)` 조회
2. **활성 제공자 결정**: `active_provider`가 설정돼 있고 해당 키가 비어있지 않으면 그 제공자를
   사용. `active_provider`가 비어있더라도 비어있지 않은 키가 정확히 1개면 그 키를 사용(방어 로직).
3. 결정된 provider+key가 있으면 → `ai_provider.call_ai(prompt, provider, api_key)`
4. 성공 시 → `(QuestionSet, True)` 반환
5. 실패 또는 키 없음 → 기존 `_generate_with_opencode(prompt)` fallback

> 활성 제공자 결정 로직은 세 서비스 함수에서 반복되므로 `api_key_store`에
> `resolve_active(welfare_id) -> tuple[str, str] | None`(provider, key) 헬퍼로 추출해 재사용한다.

#### `public_data.py:refine_topic_question()`

동일한 패턴으로 `welfare_id` 파라미터 추가.

#### `public_data.py:generate_artifact_analysis()`

동일한 패턴으로 `welfare_id` 파라미터 추가.

#### `claude.py:generate_text()`

```python
async def generate_text(
    prompt: str,
    max_tokens: int = 1500,
    provider: str | None = None,       # ← 추가
    api_key: str | None = None,        # ← 추가
) -> str:
```

로직:
1. `provider`와 `api_key`가 모두 있으면 → `ai_provider.call_ai(prompt, provider, api_key)` 우선 시도
2. 실패하거나 없으면 → 기존 Claude → OpenCode fallback 유지

#### `essay.py:generate_essay()`

```python
async def generate_essay(
    ...,
    welfare_id: str | None = None,     # ← 추가
) -> tuple[str, str, int, dict[str, int]]:
```

로직:
1. `welfare_id`가 있으면 → `api_key_store.resolve_active(welfare_id)` 로 provider+key 결정
2. provider+key가 있으면 → `generate_text(prompt, provider=..., api_key=...)` 전달
3. 없으면 → 기존 방식 유지

> **welfare_id 출처**: `essay/generate`는 본래 `topic_id` 기반 엔드포인트이고
> `WeeklyTopic`이 이미 소유자 `welfare_id`를 가진다(`welfare.py` 다수 사용처 확인됨).
> 따라서 별도 쿼리 파라미터를 추가하기보다 **대상 주제(`WeeklyTopic.welfare_id`)에서
> 소유 복지사를 역참조**하는 방식을 우선 채택한다(데이터 일관성·프론트 수정 최소화).
> 단, 중앙 기본 주제처럼 `welfare_id`가 `None`인 경우는 시스템 fallback으로 처리한다.

### 2-6. 엔드포인트 수정 (welfare.py / essay.py)

각 엔드포인트에서 `welfare_id`를 추출하여 서비스 함수에 전달:
```python
@router.post("/topics/generate-questions")
async def generate_questions(body: GenerateQuestionsRequest):
    qset, ai_generated = await generate_topic_question(
        welfare_id=body.welfare_id,    # ← 전달
        title=body.title,
        ...
    )
```

### 2-7. 설정 추가 (`app/config.py`)

```python
class Settings(BaseSettings):
    ...
    ium_api_key_encryption_key: str = ""   # ← 추가: API 키 암호화용
```

### 2-8. 의존성 추가 (`requirements.txt`)

```
cryptography>=42.0.0    # ← 추가: Fernet 암호화
```

- `httpx`는 기존 코드(`claude.py`)에서 이미 사용 중이므로 OpenAI/Gemini REST 호출에 그대로 재사용 (추가 불필요)
- `anthropic` SDK도 기존 설치됨 (추가 불필요)
- **`openai` SDK는 추가하지 않음** — 2-2 결정대로 OpenAI도 httpx REST 호출 사용

---

## 3. 프론트엔드 설계

### 3-1. 신규 페이지: `SettingsPage.tsx`

**파일 위치**: `ium/dashboard/src/pages/SettingsPage.tsx`

**UI 구성**:
```
┌──────────────────────────────────────────────────────┐
│  🔑 API 설정                                         │
│                                                      │
│  ┌─ Claude ──────────────────────────────────────┐   │
│  │  [●●●●●●●●●●●●●●●abcd]  👁  ✅ 저장됨        │   │
│  │  ┌──────────────────────────────────────────┐  │   │
│  │  │  새 API 키를 입력하세요...                │  │   │
│  │  └──────────────────────────────────────────┘  │   │
│  └────────────────────────────────────────────────┘   │
│  ┌─ OpenAI (GPT) ────────────────────────────────┐   │
│  │  [                                           ]   │   │
│  │  ┌──────────────────────────────────────────┐  │   │
│  │  │  새 API 키를 입력하세요...                │  │   │
│  │  └──────────────────────────────────────────┘  │   │
│  └────────────────────────────────────────────────┘   │
│  ┌─ Google Gemini ───────────────────────────────┐   │
│  │  [●●●●●●●●●●●●●●●wxyz]  👁  ✅ 저장됨        │   │
│  │  ┌──────────────────────────────────────────┐  │   │
│  │  │  새 API 키를 입력하세요...                │  │   │
│  │  └──────────────────────────────────────────┘  │   │
│  └────────────────────────────────────────────────┘   │
│                                                      │
│  ─── 활성 API 선택 ───                                │
│  (2개 이상 저장 시 선택 가능)                          │
│                                                      │
│  ○ Claude    ● GPT    ○ Gemini                       │
│                                                      │
│  ┌──────────────────────────────────────────────────┐ │
│  │                  💾 저장                          │ │
│  └──────────────────────────────────────────────────┘ │
│                                                      │
│  ※ API 키는 서버에 암호화되어 저장됩니다.              │
└──────────────────────────────────────────────────────┘
```

**주요 기능**:
- 각 제공자별로 저장된 키 상태 표시 (마스킹 + "저장됨" 배지)
- 입력 필드는 `type="password"` + 👁 토글 버튼으로 show/hide
- **2개 이상** 키가 저장된 경우에만 라디오 버튼 그룹 표시
- 저장 버튼 → `PUT /api/welfare/api-keys` 호출
- 웰페어 선택 드롭다운 (상단, `selectedWelfareId`)

**상태 관리**:
```typescript
const [keys, setKeys] = useState({ claude: "", openai: "", gemini: "" });
const [activeProvider, setActiveProvider] = useState("");
const [savedKeys, setSavedKeys] = useState({ claude: false, openai: false, gemini: false });
const [showKey, setShowKey] = useState({ claude: false, openai: false, gemini: false });
```

### 3-2. 신규 API 모듈: `api/settings.ts`

**파일 위치**: `ium/dashboard/src/api/settings.ts`

```typescript
const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export interface ApiKeysResponse {
  claude: string;
  openai: string;
  gemini: string;
  active_provider: string;
}

export interface ApiKeysSaveRequest {
  welfare_id: string;
  claude: string;
  openai: string;
  gemini: string;
  active_provider: string;
}

export const getApiKeys = (welfareId: string) =>
  axios.get<ApiKeysResponse>(`${API}/api/welfare/api-keys`, {
    params: { welfare_id: welfareId },
  });

export const saveApiKeys = (data: ApiKeysSaveRequest) =>
  axios.put(`${API}/api/welfare/api-keys`, data);
```

### 3-3. 내비게이션 수정 (`App.tsx`)

탭 배열에 `["settings", "🔑 API 설정"]` 추가:
```typescript
const tabs = [
  ["dashboard", "📊 이용자 모니터링"],
  ["topics", "📋 주간 주제 관리"],
  ["surveys", "📋 설문지 통합 관리"],
  ["settings", "🔑 API 설정"],           // ← 추가
  ["accounts", "🔑 계정 관리"],
  ...(isAdmin ? [["admin", "🛠 관리자"]] : []),
];
```

### 3-4. 주제 생성 화면 수정 (`TopicManager.tsx`)

`generateSurveyQuestions()` 함수에서 payload에 `welfare_id` 포함:
```typescript
const payload = {
  title: candidate.title,
  description: candidate.description ?? "",
  media_type: candidate.media_type,
  target_age: "elderly",
  question_type: qType,
  welfare_id: selectedWelfareId,          // ← 추가
};
```

`handleRefine()` 함수에서도 동일하게 `welfare_id` 포함:
```typescript
const payload = {
  topic_title: selected.title,
  current_question_set: currentQS,
  instruction: instruction,
  welfare_id: selectedWelfareId,          // ← 추가
};
```

---

## 4. 데이터 흐름

### 4-1. 조회 흐름 (GET)

```
SettingsPage (마운트)
  → GET /api/welfare/api-keys?welfare_id=xxx
  → welfare.py get_api_keys()
    → api_key_store.get_worker_keys(welfare_id)
      → load_all() → 복호화 → 해당 worker 키 추출
    → 마스킹 처리
  → 응답 반환
  → SettingsPage에 표시
```

### 4-2. 저장 흐름 (PUT)

```
SettingsPage (저장 버튼)
  → PUT /api/welfare/api-keys { welfare_id, claude, openai, gemini, active_provider }
  → welfare.py save_api_keys()
    → api_key_store.set_worker_keys(welfare_id, keys)
      → load_all() → merge → save_all() → 암호화 → 파일 저장
  → {"status": "ok"} 반환
```

### 4-3. AI 호출 흐름 (topic/essay)

```
TopicManager / SurveyManager
  → AI 호출 API (welfare_id 포함)
  → router → service
    → api_key_store.get_worker_keys(welfare_id)
    → active_provider + api_key 확인
      ├─ 있음 → ai_provider.call_ai(prompt, provider, key)
      │         → 해당 AI 호출 → 성공 시 반환
      │         → 실패 시 fallback
      └─ 없음 → 기존 시스템 설정 사용
```

---

## 5. 파일 목록

### 신규 파일 (4개)

| # | 파일 | 설명 |
|:-:|------|------|
| 1 | `ium/backend/app/services/api_key_store.py` | 암호화 파일 저장/로드 서비스 |
| 2 | `ium/backend/app/services/ai_provider.py` | Claude/GPT/Gemini 통합 호출 서비스 |
| 3 | `ium/dashboard/src/pages/SettingsPage.tsx` | API 키 설정 UI |
| 4 | `ium/dashboard/src/api/settings.ts` | API 키 CRUD API 호출 모듈 |

### 수정 파일 (8개)

| # | 파일 | 변경 내용 |
|:-:|------|-----------|
| 1 | `ium/backend/requirements.txt` | `cryptography` 추가 |
| 2 | `ium/backend/app/config.py` | `ium_api_key_encryption_key` 설정 추가 |
| 3 | `ium/backend/app/routers/welfare.py` | API 키 엔드포인트 추가 + Request 모델에 welfare_id |
| 4 | `ium/backend/app/routers/essay.py` | essay/generate에서 대상 `WeeklyTopic.welfare_id` 역참조하여 essay 서비스에 전달 |
| 5 | `ium/backend/app/services/public_data.py` | `generate_topic_question()` 등에 welfare_id 파라미터 |
| 6 | `ium/backend/app/services/claude.py` | `generate_text()`에 provider/api_key 파라미터 |
| 7 | `ium/backend/app/services/essay.py` | `generate_essay()`에 welfare_id 파라미터 |
| 8 | `ium/dashboard/src/App.tsx` | 탭에 "API 설정" 추가 |
| 9 | `ium/dashboard/src/pages/TopicManager.tsx` | generate-questions 등에 welfare_id 포함 |

### 생성 파일 (1개)

| # | 파일 | 설명 |
|:-:|------|------|
| 1 | `ium/backend/data/api_keys.enc` | 암호화된 API 키 저장 파일 (최초 저장 시 생성) |

---

## 6. 보안 고려사항

| 항목 | 처리 방안 |
|------|-----------|
| **접근 제어** | `GET/PUT /api/welfare/api-keys`는 요청자와 `welfare_id` 일치 검증(또는 최소 `WelfareWorker` 존재 확인). `welfare_id`만으로 타인 키 조회/수정 불가 (2-3 참조) |
| **키 저장** | Fernet(AES-256-CBC + HMAC) 암호화 후 파일 저장 |
| **암호화 키** | **운영: 환경변수 `IUM_API_KEY_ENCRYPTION_KEY` 권장.** `.api_key_encryption_key` 파일 방식은 암호문과 동일 디렉터리에 키가 놓여 at-rest 보호 효과가 제한적임(2-1 한계 명시). 키 파일은 `.gitignore` 등록 |
| **키 전송** | HTTPS 환경에서 전송 (현재 로컬 개발이므로 추후 고려) |
| **키 노출** | API 응답 시 마스킹 처리 (마지막 4자리만 노출). 키 길이 8자 미만이면 전체 마스킹 |
| **파일 권한** | `api_keys.enc` / `.api_key_encryption_key`는 OS 파일 권한으로 보호 (소유자만 읽기) |
| **메모리** | 복호화된 데이터는 요청 처리 후 GC에 의해 해제 |

---

## 7. fallback 정책

| 상황 | 동작 |
|------|------|
| `welfare_id` 미제공 | 시스템 설정(`settings.anthropic_api_key` / `settings.opencode_api_key`) 사용 |
| API 키 파일 없음 | 시스템 설정 사용 |
| 복지사 키 없음 | 시스템 설정 사용 |
| `active_provider`가 가리키는 키가 빈 문자열 | 시스템 설정 사용 |
| AI 호출 실패 (네트워크/인증) | 기존 fallback 체인 실행 |
| 모든 AI 실패 | 기존 하드코딩 템플릿 사용 (topic) 또는 에러 반환 (essay) |

---

## 8. 테스트 계획

### 8-1. 백엔드 단위 테스트

| 테스트 | 내용 |
|--------|------|
| 암호화 저장/복호화 | `api_key_store.save_all()` → `load_all()` → 데이터 일치 확인 |
| 키 마스킹 | `****...abcd` 형식 확인 |
| AI 제공자 호출 | 각 provider별 mock 호출 테스트 |
| fallback | 키 없을 때 시스템 설정 사용 확인 |

### 8-2. 통합 테스트

| 테스트 | 내용 |
|--------|------|
| API 키 저장 후 조회 | PUT → GET → 마스킹된 값 일치 |
| 접근 제어 | 타인 `welfare_id`로 GET/PUT 시 거부(403/검증 실패) 확인 |
| 키 1개 자동 활성화 | 키 1개만 저장 → `active_provider` 자동 설정 → AI 호출에 해당 키 사용 확인 |
| API 키로 주제 생성 | 키 저장 → generate-questions → AI 호출 성공 |
| API 키 없을 때 주제 생성 | 키 삭제 → generate-questions → 시스템 fallback |
| 작품 생성 | API 키 저장 → essay/generate → AI 호출 성공 |

### 8-3. 프론트엔드

| 테스트 | 내용 |
|--------|------|
| 입력 필드 렌더링 | 3개 제공자 각각 입력 필드 확인 |
| show/hide 토글 | password ↔ text 전환 확인 |
| 라디오 버튼 조건부 표시 | 1개 키 저장 시 숨김, 2개 저장 시 표시 |
| 저장 버튼 동작 | API 호출 성공/실패 토스트 메시지 |

---

## 9. 마이그레이션 / 호환성

- **기존 데이터 영향 없음**: 새로운 `.enc` 파일로 관리, DB 변경 없음
- **기존 API 호환성**: `welfare_id`는 `Optional`이므로 기존 클라이언트 영향 없음
- **프론트 탭**: 기존 탭 순서 유지, "API 설정"만 추가
