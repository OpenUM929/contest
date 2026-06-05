# Pipeline F — 복지사 알림 · 대시보드 상세 구현 계획

> **의존**: Pipeline E (알림 트리거)  
> **영향**: 없음 (최종 단계)  
> **작성 기준일**: 2026년 6월 1일

---

## 현재 코드 상태 (진단)

| 파일 | 위치 | 현재 상태 | 문제 |
|---|---|---|---|
| `dashboard/src/pages/Dashboard.tsx` | 41~44번 줄 | `resolveAlert()` — `fetchDashboard()` 재호출만 | PATCH 요청 미전송. 알림 실제 해결 안 됨 |
| `dashboard/src/pages/Dashboard.tsx` | 109~130번 줄 | 전화/방문/상담/상세 버튼 | onClick 핸들러 없음 (모두 dummy) |
| `backend/app/routers/welfare.py` | 52~58번 줄 | 위험도: 최신 감정 1건만 | 복합 조건 미반영 |
| `backend/app/services/alert.py` | 36번 줄 | `logger.warning` | 실제 알림 채널 없음 (E에서 처리) |
| `backend/app/routers/welfare.py` | 전체 | 개입 이력 조회 없음 | 복지사 활동 기록 불가 |

---

## 구현 목표

```
[Fix 1] resolveAlert → PATCH /safety/alerts/{id}/resolve 실제 호출
[Fix 2] 위험도 복합 조건 (감정 + 접속 + 알림 종합)
[Feature 1] 복지사 행동 버튼 연결 (전화/방문/상담)
[Feature 2] 개입 이력 기록 및 조회
[Feature 3] 알림 미해결 건수 배지
```

---

## Fix 1 — resolveAlert 수정

### 문제 코드 (`Dashboard.tsx` 41~44번 줄)

```typescript
// 현재 (버그): alert_id 없이 단순 재조회
const resolveAlert = async (userId: string) => {
  // 실제로는 alert_id 필요 — 데모용 단순화
  await fetchDashboard();
};
```

### 수정 방향

대시보드 데이터에 `alert_id` 포함 필요.

#### 백엔드 수정 — `/welfare/dashboard` 응답에 alert_id 포함

**파일**: `backend/app/routers/welfare.py`

```python
# alert_id 목록 포함
alert_result = await db.execute(
    select(SafetyAlert.id, SafetyAlert.alert_type, SafetyAlert.severity)
    .where(SafetyAlert.user_id == user.id, SafetyAlert.resolved == False)
    .order_by(SafetyAlert.created_at.desc())
)
active_alert_rows = alert_result.all()
active_alerts_count = len(active_alert_rows)
active_alert_ids = [str(r.id) for r in active_alert_rows]

summary.append({
    "user_id": str(user.id),
    "nickname": user.nickname,
    "level": level,
    "last_seen": user.last_seen_at.isoformat() if user.last_seen_at else None,
    "active_alerts": active_alerts_count,
    "active_alert_ids": active_alert_ids,  # 추가
    "latest_emotion": latest_emotion,
})
```

#### 프론트엔드 수정 — 실제 PATCH 호출

**파일**: `dashboard/src/pages/Dashboard.tsx`

```typescript
// 타입 업데이트
interface UserSummary {
  user_id: string;
  nickname: string;
  level: "red" | "yellow" | "green";
  last_seen: string | null;
  active_alerts: number;
  active_alert_ids: string[];  // 추가
  latest_emotion: string | null;
}

// resolveAlert 수정
const resolveAlert = async (userId: string, alertIds: string[]) => {
  // 모든 미해결 알림을 순서대로 해결
  for (const alertId of alertIds) {
    await axios.patch(`${API}/safety/alerts/${alertId}/resolve`);
  }
  // 해결 후 대시보드 갱신
  await fetchDashboard();
};
```

**버튼 연결**:

```typescript
{selected === user.user_id && (
  <div style={styles.actionRow}>
    <button
      style={{ ...styles.actionBtn, background: "#E8572A" }}
      onClick={(e) => {
        e.stopPropagation();
        window.open(`tel:${user.phone ?? ""}`, "_self");  // 전화 기능
      }}
    >
      📞 전화하기
    </button>
    <button style={{ ...styles.actionBtn, background: "#555" }}
      onClick={(e) => {
        e.stopPropagation();
        recordIntervention(user.user_id, "visit");  // 방문 기록
      }}
    >
      🏠 방문 요청
    </button>
    <button style={{ ...styles.actionBtn, background: "#4CAF50" }}
      onClick={(e) => {
        e.stopPropagation();
        recordIntervention(user.user_id, "counseling");  // 상담 연결
      }}
    >
      🔗 상담 연결
    </button>
    <button
      style={{ ...styles.actionBtn, background: "#9C27B0" }}
      onClick={(e) => {
        e.stopPropagation();
        window.open(`/welfare/users/${user.user_id}`, "_blank");
      }}
    >
      📋 상세 보기
    </button>
    {user.active_alerts > 0 && (
      <button
        style={{ ...styles.actionBtn, background: "#888" }}
        onClick={(e) => {
          e.stopPropagation();
          resolveAlert(user.user_id, user.active_alert_ids);
        }}
      >
        ✅ 알림 해결
      </button>
    )}
  </div>
)}
```

---

## Fix 2 — 위험도 복합 조건 (Pipeline C에서 정의된 함수 연동)

**파일**: `backend/app/routers/welfare.py`

현재 단순 조건:
```python
if no_contact or active_alerts > 0:
    level = "red"
elif latest_emotion == "negative":
    level = "yellow"
else:
    level = "green"
```

**Pipeline C의 `compute_risk_level()` 연동**:

```python
from app.services.alert import get_recent_emotions
from app.services.emotion import check_emotion_trend

# 기존 단순 조건 대신
recent_emotions = await get_recent_emotions(db, str(user.id), days=7)
emotion_trend = await check_emotion_trend(recent_emotions)

# 복합 위험도 계산
if (no_contact and active_alerts_count > 0) or emotion_trend == "red":
    level = "red"
elif no_contact or active_alerts_count > 0 or emotion_trend == "yellow":
    level = "yellow"
else:
    level = "green"
```

---

## Feature 1 — 개입 이력 기록 API

### 모델 추가

**파일**: `backend/app/models/models.py`

```python
class InterventionLog(Base):
    __tablename__ = "intervention_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    welfare_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("welfare_workers.id"))
    action_type: Mapped[str] = mapped_column(String(30))   # call | visit | counseling | resolve
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

**init.sql 추가**:
```sql
CREATE TABLE IF NOT EXISTS intervention_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    welfare_id UUID REFERENCES welfare_workers(id),
    action_type VARCHAR(30) NOT NULL,
    note TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### API 추가

**파일**: `backend/app/routers/welfare.py`

```python
class InterventionCreate(BaseModel):
    action_type: str   # call | visit | counseling | resolve
    note: str | None = None
    welfare_id: str | None = None


@router.post("/users/{user_id}/intervention", summary="개입 이력 기록")
async def record_intervention(
    user_id: str,
    body: InterventionCreate,
    db: AsyncSession = Depends(get_db),
):
    log = InterventionLog(
        user_id=uuid.UUID(user_id),
        welfare_id=uuid.UUID(body.welfare_id) if body.welfare_id else None,
        action_type=body.action_type,
        note=body.note,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return {
        "log_id": str(log.id),
        "action_type": log.action_type,
        "created_at": log.created_at.isoformat(),
    }


@router.get("/users/{user_id}/interventions", summary="개입 이력 조회")
async def list_interventions(
    user_id: str,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(InterventionLog)
        .where(InterventionLog.user_id == uuid.UUID(user_id))
        .order_by(InterventionLog.created_at.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    return [
        {
            "log_id": str(l.id),
            "action_type": l.action_type,
            "note": l.note,
            "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]
```

### 프론트엔드 개입 기록 함수

**파일**: `dashboard/src/pages/Dashboard.tsx`

```typescript
const recordIntervention = async (
  userId: string,
  actionType: "call" | "visit" | "counseling" | "resolve",
  note?: string,
) => {
  await axios.post(`${API}/welfare/users/${userId}/intervention`, {
    action_type: actionType,
    note: note ?? "",
  });
  // 성공 피드백
  alert(`${actionType} 기록이 저장되었습니다.`);
  await fetchDashboard();
};
```

---

## Feature 2 — 사용자 상세 화면 개입 이력 표시

현재 `welfare.py`의 `user_detail()`은 최근 대화 + 알림만 반환.  
개입 이력 추가:

```python
@router.get("/users/{user_id}/detail")
async def user_detail(user_id: str, db: AsyncSession = Depends(get_db)):
    ...
    
    # 개입 이력 추가
    intervention_result = await db.execute(
        select(InterventionLog)
        .where(InterventionLog.user_id == uuid.UUID(user_id))
        .order_by(InterventionLog.created_at.desc())
        .limit(10)
    )
    interventions = intervention_result.scalars().all()
    
    return {
        ...기존 필드...,
        "interventions": [
            {
                "type": l.action_type,
                "note": l.note,
                "date": l.created_at.isoformat(),
            }
            for l in interventions
        ],
    }
```

---

## Feature 3 — 실시간 알림 (선택적 구현)

현재 대시보드는 1분마다 폴링 (`setInterval`).  
FCM(Firebase Cloud Messaging) 또는 WebSocket을 통한 실시간 알림은 Phase 2.

**Phase 1 개선**: 폴링 주기 최적화 + 새 알림 시 시각적 강조

```typescript
useEffect(() => {
  fetchDashboard();
  const interval = setInterval(async () => {
    const prevData = data;
    await fetchDashboard();
    // 새 red 알림 감지 시 브라우저 알림
    if (data && prevData && data.summary.red > prevData.summary.red) {
      if (Notification.permission === "granted") {
        new Notification("이음 긴급 알림", {
          body: "긴급 상태 이용자가 증가했습니다. 대시보드를 확인하세요.",
        });
      }
    }
  }, 30_000); // 30초로 단축
  
  // 브라우저 알림 권한 요청
  if (Notification.permission === "default") {
    Notification.requestPermission();
  }
  
  return () => clearInterval(interval);
}, []);
```

---

## 변경 파일 요약

| 파일 | 변경 내용 | 우선순위 |
|---|---|---|
| `dashboard/src/pages/Dashboard.tsx` | resolveAlert PATCH 연결, 버튼 핸들러, 브라우저 알림 | 🔴 |
| `backend/app/routers/welfare.py` | active_alert_ids 응답 추가, 위험도 복합 조건, 개입 이력 API | 🔴 |
| `backend/app/models/models.py` | `InterventionLog` 모델 추가 | 🟡 |
| `backend/app/init.sql` | `intervention_logs` 테이블 추가 | 🟡 |

---

## 테스트 시나리오

1. **resolveAlert**: 대시보드에서 "알림 해결" 클릭 → DB `safety_alerts.resolved = true` 확인
2. **위험도 복합**: 7일 연속 부정 감정 + 2일 미접속 → "red" 판정 확인
3. **개입 기록**: "전화하기" 클릭 → `intervention_logs` 테이블에 레코드 생성 확인
4. **상세 화면**: `/welfare/users/{id}/detail` 응답에 `interventions` 배열 포함 확인
5. **브라우저 알림**: red 사용자 증가 시 브라우저 알림 팝업 표시

---

> **다음 파이프라인**: G — 데이터 보안 (AES-256 암호화, 동의서)
