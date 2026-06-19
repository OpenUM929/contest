# Phase 2 — 복지사 대시보드 완성

> 상태: PND | 작성일: 2026-06-08
> 작업 유형: 기능 구현 계획
> 선행 조건: [Phase 1 완료](../이음_통합구현계획_20260604.md) ✅
> 대상 코드베이스: `C:\dev\contest\ium`

---

## 수정 이력

| 날짜 | 변경 섹션 | 변경 요약 |
|------|-----------|-----------|
| 2026-06-08 | 최초 작성 | 통합 계획서에서 Phase 2 분리 |
| 2026-06-08 | §2-작업3·4, §2-작업8, §3, §4 | 에러 처리 UX 명세 추가 / medium 위기 시나리오 추가 / Alembic 마이그레이션 검토 내용 추가 |
| 2026-06-08 | §2 전체, §4 | 검토 6항목 결정 반영: 위험도 중복 합산 의도 확정 / medium 팝업 반영 확인 / PATCH 엔드포인트 기존 구현 확인 / 전화 인텐트 기록 설계 확정 / message_cnt 활용 범위 명시 / check-all 권한 체크 명세 추가 |
| 2026-06-08 | §1, §2-작업4·5·8·9 | 구현 현황 대조 반영: 작업5(boolean→가중치 B안 확정), 작업8(3단계 C안 확정+Youth 추가), 작업4(하이브리드 모달), 작업9(완전 미구현 명시) |
| 2026-06-08 | §1 전체, §2 전체, §3 | **실제 코드베이스 대조 검증**: 작업1·2·6·7이 이미 구현됨으로 확인되어 상태 변경 / 스키마/API 불일치 사항 추가 / Phase 3 링크 TBD 처리 |
| 2026-06-08 | §2-작업2·3·5·7·8 | 검토 갭 보완: welfare_id 추출 명시 / 응답 스키마 언급 추가 / get_recent_emotions 존재 확인 주석 / 타임존 비교 안전화 / compute_risk_level 호출부 명시 / Essay.contributor_cnt 컬럼 추가 범위 명시 / triggerWelfareContact 엔드포인트 확정 |
| 2026-06-09 | §1, §2, §3, §4 | 프롬프트 안개비 재설계 후속 작업 3건 추가 (작업10: 프롬프트 즉시 수정, 작업11: question_parser 금지 패턴 검증, 작업12: Dashboard 초안 틀 UX) |
| 2026-06-09 | §1, §2-작업7·10·11·12 | 계획-코드 불일치 정정: `message_count` 확정 / 작업10·11·12 구현 완료 반영 |

---

## 목표

복지사가 대시보드를 통해 위기 알림을 해결하고, 개입 이력을 기록하며, 복합 위험도 기반으로 사용자를 관리할 수 있도록 F 파이프라인을 완성한다.  
수필 기여자 추적(`EssayContributor`) 및 위기 심각도 팝업 세분화도 이 단계에서 함께 처리한다.

---

## 1. 작업 목록

| # | 작업 | 대상 파일 | 파이프라인 | 우선순위 | 현재 상태 |
|---|---|---|---|---|---|
| 1 | **InterventionLog 모델 검토/보정** | `models.py`, `init.sql` | F | 🔴 선행 필수 | ✅ 구현됨 (스키마 불일치 보정 필요) |
| 2 | **개입 이력 API 검토/보정** | `welfare.py` | F | 🔴 선행 필수 | ✅ 구현됨 (스키마/enum 불일치 보정 필요) |
| 3 | **Dashboard resolveAlert 연결** | `Dashboard.tsx` | F | 🟡 | 🟡 부분 (Backend: `active_alert_ids` 이미 포함, Frontend 연결 확인 필요) |
| 4 | **Dashboard 버튼 핸들러 연결** | `Dashboard.tsx` | F | 🟡 | 🟡 부분 (즉시 POST, 모달 없음) |
| 5 | **위험도 복합 조건** | `welfare.py` | F | 🟡 | 🟡 부분 (`_compute_risk_level` 존재, boolean → 가중치로 교체 필요) |
| 6 | **사용자 상세 — 개입 이력 포함** | `welfare.py` | F | 🟡 | ✅ 구현됨 (`interventions` 배열 이미 포함) |
| 7 | **EssayContributor 테이블 검토/보정** | `models.py`, `init.sql`, `essay.py` | D | 🟡 | ✅ 구현됨 (스키마 불일치 및 기여자 집계 로직 확인 필요) |
| 8 | **위기 심각도별 팝업 분기** | `claude.py`, `ElderlyMain.tsx`, `YouthMain.tsx` | E/B | 🟢 | 🟡 부분 (Elderly: `high`만 분기, Youth: 분기 로직 없음) |
| 9 | **/safety/check-all API** | `safety.py` | E | 🟢 | ❌ 완전 미구현 |
| 10 | **프롬프트 즉시 수정** | `topic_publish_choice_v1.txt` | A'' | 🔴 선행 필수 | ✅ 완료 (`mixed_v1.txt` `{custom_hint}` 추가 포함, 2026-06-09) |
| 11 | **question_parser.py 금지 패턴 검증** | `question_parser.py` | A'' | 🟡 | ✅ 완료 (`validate_question_quality()` + welfare.py `warnings` 연동, 2026-06-09) |
| 12 | **Dashboard 설문지 초안 틀 UX** | `dashboard/src/pages/TopicManager.tsx` | A''/F | 🟡 | ✅ 완료 (AI 초안 배지, warnings 표시, 상태 전환, 2026-06-09) |

---

## 2. 작업 상세

### 작업 1 — InterventionLog 모델 검토/보정

**대상 파일**: `backend/app/models/models.py`, `backend/app/init.sql`

**실제 구현 상태**: `models.py:108`에 `InterventionLog` 모델이 이미 구현되어 있으며, `init.sql:93`에 테이블도 존재합니다.

**실제 구현 (현재 코드):**
```python
class InterventionLog(Base):
    __tablename__ = "intervention_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    welfare_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("welfare_workers.id"))
    action_type: Mapped[str] = mapped_column(String(50))  # phone | visit | counseling | detail | alert_resolve
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

**계획서 초안 vs 실제 불일치:**

| 항목 | 계획서 초안 | 실제 구현 | 조치 |
|------|------------|----------|------|
| `id` | `SERIAL PRIMARY KEY` | `UUID` | ✅ 실제 구현 유지 (프로젝트 표준) |
| `user_id` | `INTEGER` | `UUID` | ✅ 실제 구현 유지 |
| `welfare_id` | `NOT NULL` | `UUID \| None` (nullable) | ✅ 실제 구현 유지 — null 허용이 유연함 |
| `action_type` | `VARCHAR(20)` (`call`/`visit`/`counsel`/`other`) | `VARCHAR(50)` (`phone`/`visit`/`counseling`/`detail`/`alert_resolve`) | ⚠️ **enum 값 통일 필요** (see §5.1) |

> **결론**: 모델 자체는 이미 구현되어 있음. `action_type` enum 값 통일만 필요.

---

### 작업 2 — 개입 이력 API 검토/보정

**대상 파일**: `backend/app/routers/welfare.py`

**실제 구현 상태**: `welfare.py:867`에 `POST /welfare/users/{user_id}/intervention`, `welfare.py:890`에 `GET /welfare/users/{user_id}/interventions`가 이미 구현되어 있습니다.

**실제 구현 (현재 코드):**
```python
class InterventionRequest(BaseModel):
    welfare_id: str | None = None
    action_type: str  # phone | visit | counseling | detail | alert_resolve
    note: str | None = None

@router.post("/users/{user_id}/intervention", summary="개입 이력 기록")
async def record_intervention(user_id: str, body: InterventionRequest, ...):
    ...
    return {"intervention_id": str(log.id), "status": "recorded"}

@router.get("/users/{user_id}/interventions", summary="사용자 개입 이력 조회")
async def get_interventions(user_id: str, limit: int = 20, ...):
    ...
    return [{"id": str(l.id), "action_type": l.action_type, "note": l.note, "created_at": l.created_at.isoformat()}]
```

**계획서 초안 vs 실제 불일치:**

| 항목 | 계획서 초안 | 실제 구현 | 조치 |
|------|------------|----------|------|
| `welfare_id` | Body에 없음 | `str \| None` (optional) | ✅ 실제 구현 유지 |
| `action_type` | `Literal["call","visit","counsel","other"]` | `str` (값: `phone`/`visit`/`counseling`/`detail`/`alert_resolve`) | ⚠️ **enum 통일 필요** |
| 응답 필드 | `user_id`, `welfare_id` 포함 | `intervention_id`, `status`만 반환 | ℹ️ **POST 응답은 간결 유지, GET 응답은 상세** |
| 응답 필드명 | `created_at` | `created_at` (ISO string) | ✅ 일치 |

> **결론**: API 엔드포인트는 이미 구현되어 있음. `action_type` enum 값과 프론트엔드 연결만 확인 필요.

**구현 주의 — `welfare_id` 추출:**

`welfare_id`는 요청 바디가 아니라 **인증 토큰에서 추출**한다. 클라이언트가 임의로 전달할 수 없도록 한다.

```python
@router.post("/users/{user_id}/intervention", status_code=201)
def create_intervention(
    user_id: int,
    body: InterventionCreate,
    current_welfare: WelfareWorker = Depends(get_current_welfare_worker),
    db: Session = Depends(get_db)
):
    log = InterventionLog(
        user_id=user_id,
        welfare_id=current_welfare.id,   # ← 토큰에서 추출, 바디 아님
        action_type=body.action_type,
        note=body.note,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
```

---

### 작업 3 — Dashboard resolveAlert 연결

**대상 파일**: `dashboard/src/pages/Dashboard.tsx`

> ✅ **엔드포인트 기존 구현 확인**: `PATCH /safety/alerts/{alert_id}/resolve`는 Phase 1에서 `backend/app/routers/safety.py`에 이미 구현되어 있다. **이 작업에서 별도 추가 불필요.** 프론트엔드에서 호출만 연결하면 된다.

**변경 사항:**
1. ~~`/welfare/dashboard` 응답에 `active_alert_ids` 필드 추가~~ → **이미 구현됨** (`welfare.py:105`)
2. 프론트: "알림 해결" 버튼 클릭 시 기존 `PATCH /safety/alerts/{id}/resolve` 호출 연결
3. 성공 후 해당 사용자 카드에서 경고 배지 제거 (local state 업데이트)

**Backend 확인 (`welfare.py` `/welfare/dashboard`):**
```python
# 이미 구현되어 있음 (welfare.py:105)
"active_alert_ids": active_alert_ids,
```

> ✅ **응답 스키마 확인**: `/welfare/dashboard`는 현재 `dict`로 직접 반환하고 있어 `active_alert_ids`가 이미 포함되어 있음. 별도 Pydantic 모델 변경 불필요.

**에러 처리 (프론트엔드 UX):**

| 상황 | UX 처리 |
|------|---------|
| PATCH 성공 | 낙관적 업데이트 — 배지 즉시 제거, 초록 토스트 "알림이 해결되었습니다" |
| PATCH 실패 (4xx/5xx) | 배지 원복 + 빨간 토스트 "알림 해결에 실패했습니다. 다시 시도해주세요" |
| 네트워크 오류 | 배지 원복 + 노란 토스트 "네트워크 오류. 연결을 확인해주세요" |

---

### 작업 4 — Dashboard 버튼 핸들러 연결

**대상 파일**: `dashboard/src/pages/Dashboard.tsx`

**현재 구현**: 모든 버튼이 즉시 `POST /intervention` 호출 (note 하드코딩). **하이브리드 방식으로 교체한다.**

| 버튼 | 결정된 동작 | 이유 |
|------|------------|------|
| 전화하기 | `window.open('tel:...')` + `POST /intervention` **즉시 기록** (note 생략) | 통화 중 입력 불가. 인텐트 기록이 목적. |
| 방문하기 | **모달 열기** → note 선택 입력 → `POST /intervention` | 방문 상황 메모 필요. note 없이도 저장 가능(optional). |
| 상담하기 | **모달 열기** → note 선택 입력 → `POST /intervention` | 상담 내용 메모 필요. note 없이도 저장 가능(optional). |
| 상세 보기 | `/users/${user.id}` 상세 화면 이동 | 변경 없음 |
| 알림 해결 | `PATCH /safety/alerts/{id}/resolve` (작업 3) | 변경 없음 |

> **변경 범위**: 현재 즉시 POST → 방문/상담만 모달 추가. 전화하기는 현재 방식 유지.  
> 모달에서 note는 `<textarea placeholder="상황 메모 (선택)">` — 비워도 저장 가능하여 UX 부담 최소화.

**에러 처리 (프론트엔드 UX):**

| 상황 | UX 처리 |
|------|---------|
| POST 성공 | modal 닫기 + 초록 토스트 "개입 이력이 기록되었습니다" |
| POST 실패 (4xx/5xx) | modal 유지 + 빨간 토스트 "기록에 실패했습니다. 다시 시도해주세요" |
| 네트워크 오류 | modal 유지 + 노란 토스트 "네트워크 오류. 연결을 확인해주세요" |
| 전화하기 — POST 실패 | 전화 연결은 이미 시작됐으므로 modal 없이 토스트로만 알림 (전화 취소 안 함) |

---

### 작업 5 — 위험도 복합 조건

**대상 파일**: `backend/app/routers/welfare.py`

**현재 구현 (교체 대상):**
```python
# welfare.py — 단순 boolean 우선순위 분기
if no_contact:      return "red"
if active_alert:    return "red"
if negative_emotion: return "yellow"
return "green"
```
> ⚠️ 문제: 미해결 Alert 1개만 있어도 no_contact 없이 red 판정. 부정 감정 1건만 있어도 yellow. 오탐률 높음.

**결정: B안(가중치 누적 방식)으로 교체.** `compute_risk_level()` 함수로 격리하여 기존 호출부 변경 최소화.

> **호출부 교체 대상**: `welfare.py`의 `/welfare/dashboard` 핸들러 내 `risk_level` 산정 분기문 (현재 `if no_contact: return "red"` 로직)을 `compute_risk_level(user.id, db)` 단일 호출로 교체한다.

```
조건 점수 합산:
  - 3일 이상 미접속                  → +3
  - 미해결 SafetyAlert 존재          → +3
  - 최근 7일 부정 감정 비율 > 60%    → +2  ← 지속적 추세 포착
  - 최근 3일 부정 감정 비율 > 80%    → +1  ← 급격한 악화 보너스 (동시 충족 가능, 의도된 중복 합산)
  - 최근 7일 접속 횟수 < 2           → +1

점수 → 위험도:
  6+  → "red"
  3~5 → "yellow"
  0~2 → "green"

최대 가능 점수: 3+3+2+1+1 = 10점
```

**구현 스케치:**
```python
def compute_risk_level(user_id: uuid.UUID, db: Session) -> str:
    score = 0
    now = datetime.now(timezone.utc)

    # 미접속 — DB 레벨 비교로 타임존 불일치 방지
    cutoff_3d = now - timedelta(days=3)
    has_recent = db.query(Conversation).filter(
        Conversation.user_id == user_id,
        Conversation.created_at >= cutoff_3d
    ).first()
    if not has_recent:
        score += 3

    # 미해결 Alert
    if db.query(SafetyAlert).filter_by(user_id=user_id, resolved=False).count():
        score += 3

    # 7일 부정 감정 비율
    # ⚠️ get_recent_emotions()가 welfare.py에 없으면 신규 구현 필요
    #    기대 시그니처: get_recent_emotions(user_id, db, days) → List[Emotion]
    recent_7d = get_recent_emotions(user_id, db, days=7)
    if recent_7d:
        neg_ratio_7d = sum(1 for e in recent_7d if e.sentiment == "negative") / len(recent_7d)
        if neg_ratio_7d > 0.6:
            score += 2
        cutoff_3d_ts = now - timedelta(days=3)
        recent_3d = [e for e in recent_7d if e.created_at >= cutoff_3d_ts]
        if recent_3d:
            neg_ratio_3d = sum(1 for e in recent_3d if e.sentiment == "negative") / len(recent_3d)
            if neg_ratio_3d > 0.8:
                score += 1

    # 7일 접속 빈도
    session_cnt = db.query(Conversation).filter(
        Conversation.user_id == user_id,
        Conversation.created_at >= now - timedelta(days=7)
    ).count()
    if session_cnt < 2:
        score += 1

    if score >= 6: return "red"
    if score >= 3: return "yellow"
    return "green"
```

> **타임존 처리 변경 요약**: `last_seen`을 Python에서 빼는 방식 대신 DB 쿼리에서 `>= cutoff` 비교로 교체했다. DB datetime이 timezone-naive로 저장된 경우 `datetime - last_seen` 연산에서 `TypeError`가 발생하므로, 동일 타입끼리 비교하는 DB 레벨 필터가 안전하다.

---

### 작업 6 — 사용자 상세 — 개입 이력 포함

**대상 파일**: `backend/app/routers/welfare.py`

**실제 구현 상태**: `GET /welfare/users/{user_id}/detail` (`welfare.py:129`) 응답에 `interventions` 배열이 **이미 포함**되어 있습니다 (`welfare.py:184`).

**실제 응답 예시:**
```json
{
  "user_id": "...",
  "nickname": "...",
  "last_seen": "...",
  "recent_conversations": [...],
  "alerts": [...],
  "interventions": [
    {
      "id": "...",
      "action_type": "phone",
      "note": "전화 연결 성공, 안부 확인",
      "date": "2026-06-07T10:00:00+00:00"
    }
  ]
}
```

> ⚠️ **필드명 주의**: 실제 응답은 `created_at` 대신 `date` 필드를 사용합니다. 프론트엔드 파싱 시 주의.

> **결론**: Backend 구현은 이미 완료됨. 프론트엔드에서 `/welfare/users/{id}/detail` 호출 시 `interventions` 배열을 사용하면 됨.

---

### 작업 7 — EssayContributor 테이블 검토/보정

**대상 파일**: `backend/app/models/models.py`, `backend/app/init.sql`, `backend/app/routers/essay.py`

**실제 구현 상태**: `models.py:119`에 `EssayContributor` 모델이 이미 구현되어 있으며, `init.sql:72`에 테이블도 존재합니다.

**실제 구현 (현재 코드):**
```python
class EssayContributor(Base):
    __tablename__ = "essay_contributors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    essay_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("essays.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    message_count: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

**계획서 초안 vs 실제 불일치:**

| 항목 | 계획서 초안 | 실제 구현 | 조치 |
|------|------------|----------|------|
| `id` | `SERIAL PRIMARY KEY` | `UUID` | ✅ 실제 구현 유지 (프로젝트 표준) |
| `essay_id` | `INTEGER` | `UUID` | ✅ 실제 구현 유지 |
| `user_id` | `INTEGER` | `UUID` | ✅ 실제 구현 유지 |
| `message_cnt` | `INTEGER NOT NULL DEFAULT 0` | `message_count INTEGER default=1` | ✅ **`message_count`로 확정** — 코드 기준으로 통일 완료 (2026-06-09) |
| `UNIQUE (essay_id, user_id)` | 있음 | **없음** | ℹ️ **중복 허용 여부 확인 필요** |

**`Essay.contributor_cnt` 컬럼 확인:**

> ⚠️ `Essay` 모델에 `contributor_cnt` 컬럼이 없다면 이 작업 범위에 추가한다. (실제 `models.py` 확인 필요)

**수필 생성 로직 확인 (`essay.py`):**

> ⚠️ `essay.py`에 기여자 집계 및 `essay_contributors` insert 로직이 있는지 확인 필요. 없다면 추가.

**`message_count` 활용 범위:**

| 용도 | 내용 |
|------|------|
| 수필 생성 내부 가중치 | 대화량이 많은 사용자의 발화를 수필 소재로 더 많이 반영 (Phase 3 프롬프트 v1 적용 시 활용) |
| API 응답 포함 여부 | **미포함** — 개인별 대화량은 프라이버시 민감 정보, 익명성 원칙 준수 |
| 향후 분석 활용 | Phase 3 `/welfare/report/anonymized`에서 익명 집계 통계로 제공 예정 |

> **결론**: 모델·테이블·기여자 집계 로직 모두 구현 완료. 필드명은 `message_count`로 확정. `UNIQUE` 제약은 미추가 상태 (동일 essay에 같은 사용자가 여러 번 기록될 수 있음 — 현재 허용).

---

### 작업 8 — 위기 심각도별 팝업 분기

**대상 파일**: `backend/app/services/claude.py`, `mobile/screens/ElderlyMain.tsx`, `mobile/screens/YouthMain.tsx`

**현재 구현 갭:**

| 위치 | 현재 상태 | 필요한 변경 |
|------|----------|------------|
| `claude.py` `stream_chat` | `[CRISIS]` 태그 유무만 파싱, 레벨 미분리 | `[CRISIS:HIGH]`/`[CRISIS:MEDIUM]`/`[CRISIS:LOW]` 태그로 교체 |
| `ElderlyMain.tsx` | `high`만 분기, `medium`/`low` 없음 | 3단계 분기 추가 |
| `YouthMain.tsx` | **존재하나** `level` 분기 없음 (모든 level 동일 처리) | Elderly와 동일하게 3단계 분기 추가 |

**결정: C안(3단계 분기) 확정.** `detect_crisis_level()`이 이미 3단계를 반환하므로 추가 비용 최소. medium과 low를 같은 팝업으로 처리하면 "복지사 연락 권유"와 "공감 토스트"의 의미 있는 UX 차이를 잃는다.

**Backend 변경 (`claude.py` `stream_chat`):**
- `detect_crisis_level()` 반환값: `"high"` | `"medium"` | `"low"` (기존 유지, 변경 없음)
- `stream_chat`에서 crisis 레벨을 `[CRISIS]` 단일 태그 대신 세분화된 태그로 삽입:
  - `[CRISIS:HIGH]`: 자해·자살 직접 표현 키워드
  - `[CRISIS:MEDIUM]`: 극단적 무기력·지속적 절망 (예: "다 포기하고 싶다", "아무것도 하기 싫다")
  - `[CRISIS:LOW]`: 일반 부정 감정 (예: "외롭다", "힘들다")
- `X-Crisis-Level` 응답 헤더는 기존과 동일하게 유지 (`high`/`medium`/`low`)

**Mobile 변경 — `ElderlyMain.tsx` + `YouthMain.tsx` (동일 로직):**
```typescript
// X-Crisis-Level 헤더 값에 따라 팝업 내용 분기 (Elderly, Youth 공통)
if (crisisLevel === 'high') {
  Alert.alert(
    "지금 힘드신가요?",
    "전문가와 바로 연결해 드릴게요.",
    [{ text: "1393 전화하기", onPress: () => Linking.openURL('tel:1393') },
     { text: "닫기", style: "cancel" }]
  );
} else if (crisisLevel === 'medium') {
  Alert.alert(
    "많이 힘드신가요?",
    "복지사 선생님께 알려드릴게요.",
    [{ text: "복지사에게 연락하기", onPress: triggerWelfareContact },
     { text: "괜찮아요", style: "cancel" }]
  );
} else if (crisisLevel === 'low') {
  // Toast — 버튼 없음, 3초 자동 소멸
  showToast("오늘 많이 힘드셨군요. 언제든 이야기해주세요.");
}
```

> **`triggerWelfareContact` 엔드포인트 확정**: 사용자 기기(모바일)에서 복지사에게 알림을 보내는 경우이므로 `POST /safety/alert` 엔드포인트를 사용한다. 이 엔드포인트가 `safety.py`에 없으면 작업 9(`/check-all`)와 함께 추가한다. 요청 바디: `{ user_id, reason: "user_request" }`, 인증: 사용자 JWT.

---

### 5.1 기존 구현 vs 계획서 초안 — 종합 불일치 정리

아래 표는 **실제 코드베이스 대조 검증** 결과, 계획서 초안과 실제 구현이 달랐던 부분을 한눈에 정리한 것입니다.

| 작업 | 계획서 초안 | 실제 구현 | 영향도 | 조치 |
|------|------------|----------|--------|------|
| 1 | `id: SERIAL`, `user_id: INTEGER` | `id: UUID`, `user_id: UUID` | **높음** | 프로젝트 표준(UUID) 유지 |
| 1 | `welfare_id: NOT NULL` | `welfare_id: UUID \| None` | **중** | null 허용이 유연함 → 유지 |
| 1 | `action_type` enum: `call`/`visit`/`counsel`/`other` | 실제 값: `phone`/`visit`/`counseling`/`detail`/`alert_resolve` | **높음** | 프론트-백 enum 통일 필요 |
| 2 | `InterventionCreate`에 `welfare_id` 없음 | `InterventionRequest`에 `welfare_id: str \| None` 있음 | **중** | API 스펙 통일 필요 |
| 2 | POST 응답: 전체 레코드 | POST 응답: `{"intervention_id", "status"}` | **중** | 프론트엔드가 응답 파싱 방식 확인 필요 |
| 6 | 응답 필드명: `created_at` | 실제 응답: `date` | **중** | 프론트엔드 파싱 오류 가능 → 필드명 통일 필요 |
| 7 | `message_cnt` | `message_count` | **중** | 필드명 통일 필요 |
| 7 | `UNIQUE (essay_id, user_id)` | 제약 없음 | **낮음** | 중복 허용 여부 정책 결정 |
| 7 | `Essay.contributor_cnt` | 확인 필요 | **중** | 없으면 추가 |
| 8 | `YouthMain.tsx` "없음" | **실제로 존재함** (분기 없음) | **중** | 계획서 오류 → 존재하므로 분기 추가만 필요 |
| 9 | `daily_safety_check` 위치 미확인 | `backend/app/services/alert.py:125` | **낮음** | 위치 확인 완료 |

> **Alembic 상태**: `backend/alembic/` 디렉토리 **존재하지 않음**. 운영 DB 마이그레이션 필요 시 `alembic init`부터 시작해야 함.

---

### 작업 9 — /safety/check-all API

**대상 파일**: `backend/app/routers/safety.py`

> ❌ **완전 미구현**: 현재 `GET /safety/check/{user_id}` (단건 조회)만 존재. `/check-all`은 새로 추가해야 한다.  
> `daily_safety_check()` 함수는 `alert.py`에 이미 구현되어 있으므로 라우터에서 이를 호출하는 엔드포인트만 추가하면 된다.

```
GET /safety/check-all
    → 전체 elder 사용자 미접속 + 감정 악화 일괄 점검
    → SafetyAlert 생성 및 이메일 발송 트리거
    → 결과 요약 반환: { checked: 50, alerts_created: 3 }
```

**구현 스케치:**
```python
@router.get("/check-all")
async def check_all(
    current_welfare: WelfareWorker = Depends(get_current_welfare_worker),
    db: Session = Depends(get_db)
):
    result = await daily_safety_check(db)  # alert.py에 이미 구현됨
    return result
```

**권한 체크 설계:**

> **결정**: 별도 `@require_admin` 데코레이터 불필요. 기존 `get_current_welfare_worker` Depends를 그대로 사용한다.  
> 복지사는 담당 사용자 전체를 일괄 점검할 권한을 가지므로, 관리자/복지사 구분 없이 복지사 인증 토큰만 있으면 접근 허용한다.

```python
@router.get("/check-all")
async def check_all_users(
    current_welfare: WelfareWorker = Depends(get_current_welfare_worker),
    db: Session = Depends(get_db)
):
    """복지사 인증 토큰 보유자만 접근 가능. 별도 admin 역할 구분 없음."""
    result = await daily_safety_check(db)
    return result
```

> 만약 향후 슈퍼어드민 개념이 추가된다면 `WelfareWorker.is_admin` 필드 체크로 확장한다 — **현재 단계에서는 복지사 토큰 인증으로 충분.**

---

### 작업 10 — 프롬프트 즉시 수정

**대상 파일**: `backend/app/prompts/topic_publish_choice_v1.txt`

**문제**: `[금지사항]` 섹션에 "최고급 강요 금지" 규칙이 누락되어 있었음. `narrative_v1.txt`, `mixed_v1.txt`, `refine_v1.txt` 3개 파일에는 모두 포함된 규칙이 `choice_v1.txt`에만 빠진 것.

**수정 내용 (✅ 완료)**:
```diff
 - '기타'라는 단어: 대신 "그 외에 문득 떠오르는 것" 등의 열린 표현 사용
+- "가장 ~한 순간", "가장 기억에 남는 ~" 등 '최고급'을 강요하는 문구 (기억이 안 난다면 실패감 유발)
```

**잔여 결정 사항** — `{custom_hint}` 일치성:

| 파일 | `{custom_hint}` | 비고 |
|------|----------------|------|
| `choice_v1.txt` | ✅ 있음 | 복지사가 보기 방향 힌트를 줄 수 있음 |
| `narrative_v1.txt` | ❌ 없음 | 서술형은 열린 공간 강조 — 힌트가 오히려 방해가 될 수 있어 의도적 제외로 판단 |
| `mixed_v1.txt` | ❌ 없음 | choice 부분이 포함되므로 추가 여부 결정 필요 |

> **제안**: `narrative`는 의도적 제외(철학적으로 맞음). `mixed`는 choice 부분이 있으므로 `{custom_hint}` 추가 권고. 복지사 확인 후 결정.

---

### 작업 11 — question_parser.py 금지 패턴 검증

**대상 파일**: `backend/app/services/question_parser.py`

**목적**: AI가 프롬프트 철학을 어기고 금지 패턴이 포함된 질문을 생성할 경우, 복지사에게 전달되기 전에 백엔드에서 감지하고 경고를 반환한다. 에러가 아닌 `warnings` 필드로 반환 — 복지사가 직접 수정 가능하므로.

**구현 스케치:**
```python
import re

PROHIBITED_PATTERNS = [
    (r"기분.*어땠", "정서 직접 묻기"),
    (r"그립.*나요", "정서 직접 묻기"),
    (r"외로.*우셨", "정서 직접 묻기"),
    (r"가장.*기억에 남는", "최고급 강요"),
    (r"가장.*좋았던", "최고급 강요"),
    (r"가장.*행복했던", "최고급 강요"),
    (r"해 주세요$", "명령형 압박"),
    (r"말씀해 주세요", "명령형 압박"),
]

def validate_question_quality(question_set: QuestionSet) -> list[str]:
    """금지 패턴 감지. 위반 문구 목록 반환 (빈 list = 통과)."""
    violations = []
    for q in question_set.questions:
        for pattern, category in PROHIBITED_PATTERNS:
            if re.search(pattern, q.text):
                violations.append(f"[{q.id}] {category}: '{q.text}'")
    return violations
```

**연동 위치**: `welfare.py`의 `/generate-questions` 핸들러에서 `parse_question_set()` 후 `validate_question_quality()` 호출. 응답에 `warnings` 필드 추가.

```python
# welfare.py /generate-questions 응답 예시
{
  "question_set": { ... },
  "warnings": ["[q1] 최고급 강요: '가장 기억에 남는 시장 풍경은?'"]  # 빈 list = 통과
}
```

---

### 작업 12 — Dashboard 설문지 초안 틀 UX

**대상 파일**: `dashboard/src/pages/TopicManager.tsx`

**목적**: 프롬프트 재설계에서 확정한 "AI 초안 → 복지사 수정 → 발행" 3단계 플로우를 대시보드 UI에 명확히 반영한다.

**변경 사항:**

| 요소 | 현재 | 변경 후 |
|------|------|---------|
| 질문 목록 헤더 | 없음 또는 미명시 | **"AI 초안"** 배지 + "복지사가 검토·수정 후 발행합니다" 안내 문구 |
| 질문 문구 | 읽기 전용 (미확인) | **인라인 편집 가능** — 각 질문 문구·보기 텍스트 직접 수정 |
| 발행 버튼 | 즉시 발행 | 수정 저장 → "검토 완료, 발행하기" 명시적 확인 단계 |
| 상태 배지 | 없음 | "AI 초안" / "수정 중" / "발행 완료" 상태 표시 |
| 경고 표시 | 없음 | `warnings` 필드 있으면 질문 옆 ⚠️ 아이콘 + 위반 내용 툴팁 |

**연동 API**: 인라인 수정 후 저장 → `POST /welfare/refine-questions`, 발행 → 기존 `POST /welfare/publish` 호출.

---

## 3. 변경 파일 요약

| 파일 | 변경 내용 | 작업 # |
|---|---|---|
| `backend/app/models/models.py` | `InterventionLog`, `EssayContributor` 모델 추가 | 1, 7 |
| `backend/app/init.sql` | `intervention_logs`, `essay_contributors` 테이블 DDL 추가 (신규 환경용) | 1, 7 |
| `backend/alembic/versions/XXXX_add_intervention_logs.py` | **신규** — 운영 DB 마이그레이션 | 1 |
| `backend/alembic/versions/XXXX_add_essay_contributors_and_contributor_cnt.py` | **신규** — 운영 DB 마이그레이션 (`essay_contributors` + `Essay.contributor_cnt`) | 7 |
| `backend/app/routers/welfare.py` | 개입 이력 API, 복합 위험도, dashboard active_alert_ids, detail interventions | 2, 3, 5, 6 |
| `backend/app/routers/essay.py` | 기여자 집계 및 `essay_contributors` insert | 7 |
| `backend/app/routers/safety.py` | `/safety/check-all` API 추가 | 9 |
| `backend/app/services/claude.py` | `stream_chat`: `[CRISIS]` → `[CRISIS:HIGH/MEDIUM/LOW]` 태그 세분화 | 8 |
| `dashboard/src/pages/Dashboard.tsx` | resolveAlert PATCH + 에러 UX, 방문/상담 모달 추가, 전화 즉시기록 유지 | 3, 4 |
| `mobile/screens/ElderlyMain.tsx` | 위기 3단계 팝업 분기 (medium/low 추가) | 8 |
| `mobile/screens/YouthMain.tsx` | 위기 3단계 팝업 분기 로직 추가 (파일 존재, 분기 없음) | 8 |
| `backend/app/prompts/topic_publish_choice_v1.txt` | `[금지사항]`에 최고급 강요 금지 추가 (✅ 수정 완료) | 10 |
| `backend/app/services/question_parser.py` | 금지 패턴 검증 로직 `validate_question_quality()` 추가 | 11 |
| `dashboard/src/pages/TopicManager.tsx` | 설문지 초안 틀 UX 반영 (초안 배지, 인라인 편집, 상태 표시, warnings 아이콘) | 12 |

---

## 4. 테스트 시나리오

| # | 시나리오 | 검증 방법 |
|---|---|---|
| T1 | resolveAlert | 대시보드에서 "알림 해결" 클릭 → DB `safety_alerts.resolved = true` 확인 |
| T2 | 개입 기록 — 전화 | "전화하기" 클릭 → `intervention_logs` 테이블에 action_type="phone" 레코드 생성 확인 |
| T3 | 개입 기록 — 방문/상담 | note 입력 후 버튼 클릭 → DB 레코드 + note 내용 확인 |
| T4 | 위험도 복합 — red 판정 | 3일 미접속 + 부정 감정 연속 → 대시보드 "red" 배지 확인 |
| T5 | 위험도 복합 — green 판정 | 정상 접속 + 긍정 감정 → "green" 확인 |
| T6 | 사용자 상세 | `/welfare/users/{id}/detail` 응답에 `interventions` 배열 포함 확인 |
| T7 | EssayContributor | 3명이 각각 2건 대화 → 수필 생성 후 `essay_contributors`에 3건, `contributor_cnt = 3` 확인 (선행: `Essay.contributor_cnt` 컬럼 마이그레이션 완료 필요) |
| T8 | HIGH 위기 팝업 | "죽고 싶어요" 메시지 → `[CRISIS:HIGH]` 감지 → "1393 전화하기" 강성 Alert 표시 확인 |
| T8-M | MEDIUM 위기 팝업 | "다 포기하고 싶어요, 아무것도 하기 싫어요" 메시지 → `[CRISIS:MEDIUM]` 감지 → "복지사에게 연락하기" 중간 Alert 표시 확인 |
| T9 | LOW 위기 팝업 | "외롭고 힘들어요" 메시지 → `[CRISIS:LOW]` 감지 → 3초 소멸 토스트 표시 확인 (Alert 없음) |
| T9-E | 에러 UX — resolveAlert | PATCH 강제 실패(서버 500) → 배지 원복 + 빨간 토스트 표시 확인 |
| T9-F | 에러 UX — 개입 기록 | POST 강제 실패 → modal 유지 + 빨간 토스트 표시 확인 |
| T10 | check-all API | `GET /safety/check-all` → 미접속 사용자 수 포함 요약 반환 확인 |
| T11 | 금지 패턴 — 최고급 강요 | "가장 기억에 남는 순간은?" 포함 질문 생성 → 응답 `warnings` 필드에 경고 문구 포함 확인 |
| T12 | 금지 패턴 — 정서 직접 | "그때 기분은 어땠나요" 포함 질문 생성 → `warnings` 필드 경고 반환 확인 |
| T13 | 초안 틀 UI | TopicManager에서 AI 생성 직후 "AI 초안" 배지 + 안내 문구 노출 확인 |
| T14 | 인라인 편집 및 발행 | 복지사가 질문 문구 수정 → 저장 → "검토 완료, 발행하기" 클릭 → 발행 완료 상태 배지 표시 확인 |
| T15 | warnings 아이콘 | 금지 패턴 포함 질문 수신 시 해당 질문 옆 ⚠️ 아이콘 및 툴팁 노출 확인 |

---

> **완료 후 다음 단계**: Phase 3 계획서 (작성 예정 / TBD)
