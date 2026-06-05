# Pipeline D — 수필 생성 · 배포 상세 구현 계획

> **의존**: Pipeline B (topic_id 저장), Pipeline A (주제 확정)  
> **영향**: 모바일 수필 수신 화면  
> **작성 기준일**: 2026년 6월 1일  
> **Critical Bug 포함** — 즉시 수정 필요

---

## 현재 코드 상태 (진단)

| 파일 | 위치 | 문제 | 심각도 |
|---|---|---|---|
| `backend/app/routers/essay.py` | 24~28번 줄 | `topic_id` 필터 없음 → 모든 주제 대화 섞임 | 🔴 Critical |
| `backend/app/routers/essay.py` | 39번 줄 | `Essay.topic_id` 저장 안 됨 | 🔴 Critical |
| `backend/app/routers/chat.py` | 71번 줄 | `topic_id=None` (B 파이프라인 문제) | 🔴 High |
| `mobile/screens/ElderlyMain.tsx` | "지난 이야기 듣기" 버튼 | `onPress` 핸들러 없음 (dummy) | 🟡 Medium |
| `backend/app/routers/essay.py` | 전체 | `essay_contributors` 중간 테이블 없음 | 🟡 Medium |
| `backend/app/services/essay.py` | 전체 | 프롬프트 v1(전문가 설계) 미적용 | 🟡 Medium |

---

## 버그 1 즉시 수정 — topic_id 필터링

### 문제 코드 (`essay.py` router 24~28번 줄)

```python
# 현재 코드 (버그)
result = await db.execute(
    select(Conversation.content)
    .where(Conversation.role == "user")
    .order_by(Conversation.created_at)
)
```

이 쿼리는 **전체 주제의 모든 대화**를 긁어옵니다.  
A라는 주제에서 나눈 대화와 B, C 주제의 대화가 모두 섞여 수필이 생성됩니다.

### 수정 코드

```python
# 수정 후
from datetime import datetime, timedelta

# 이번 주 월요일 기준
today = datetime.utcnow()
week_start = today - timedelta(days=today.weekday())
week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

# topic_id와 날짜 조건으로 필터링
if topic.get("id"):
    # DB에 저장된 주제인 경우 topic_id 기준
    topic_uuid = uuid.UUID(topic["id"])
    result = await db.execute(
        select(Conversation.content)
        .where(
            Conversation.role == "user",
            Conversation.topic_id == topic_uuid,
        )
        .order_by(Conversation.created_at)
    )
else:
    # 폴백: 이번 주 대화 (topic_id가 없는 PoC 단계)
    result = await db.execute(
        select(Conversation.content)
        .where(
            Conversation.role == "user",
            Conversation.created_at >= week_start,
        )
        .order_by(Conversation.created_at)
    )
messages = [row[0] for row in result.all()]
```

### Essay.topic_id 저장 수정 (39번 줄)

```python
# 수정 전
essay = Essay(
    title=title,
    content=content,
    contributor_cnt=len(messages),
    prompt_version=prompt_version,
)

# 수정 후
essay = Essay(
    title=title,
    content=content,
    contributor_cnt=len(messages),
    prompt_version=prompt_version,
    topic_id=uuid.UUID(topic["id"]) if topic.get("id") else None,
)
```

---

## essay_contributors 중간 테이블

수필에 기여한 사용자를 추적하기 위한 중간 테이블.  
현재 `contributor_cnt`는 대화 건수(사람 수 아님)로 부정확.

### 모델 추가

**파일**: `backend/app/models/models.py`

```python
class EssayContributor(Base):
    __tablename__ = "essay_contributors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    essay_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("essays.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    message_count: Mapped[int] = mapped_column(Integer, default=0)  # 이 사용자의 기여 메시지 수
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

### init.sql 추가

```sql
CREATE TABLE IF NOT EXISTS essay_contributors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    essay_id UUID NOT NULL REFERENCES essays(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(essay_id, user_id)
);
```

### essay.py router 수정 — 기여자 저장

```python
# 수필 생성 후 기여자 저장
from app.models.models import EssayContributor
from sqlalchemy import func

# 기여자별 메시지 수 집계
if topic.get("id"):
    contrib_result = await db.execute(
        select(Conversation.user_id, func.count(Conversation.id).label("cnt"))
        .where(
            Conversation.role == "user",
            Conversation.topic_id == topic_uuid,
        )
        .group_by(Conversation.user_id)
    )
else:
    contrib_result = await db.execute(
        select(Conversation.user_id, func.count(Conversation.id).label("cnt"))
        .where(
            Conversation.role == "user",
            Conversation.created_at >= week_start,
        )
        .group_by(Conversation.user_id)
    )

contributors = contrib_result.all()
actual_contributor_count = len(contributors)

# essay 저장 시 실제 기여자 수 사용
essay = Essay(
    title=title,
    content=content,
    contributor_cnt=actual_contributor_count,  # 메시지 수가 아닌 사용자 수
    prompt_version=prompt_version,
    topic_id=uuid.UUID(topic["id"]) if topic.get("id") else None,
)
db.add(essay)
await db.commit()
await db.refresh(essay)

# 기여자 레코드 저장
for user_id, cnt in contributors:
    contrib = EssayContributor(
        essay_id=essay.id,
        user_id=user_id,
        message_count=cnt,
    )
    db.add(contrib)
await db.commit()
```

---

## 수필 생성 서비스 (`essay.py` service) 확인

**파일**: `backend/app/services/essay.py` 확인 필요 (미열람)

현재 프롬프트 v0 사용 중. v1(전문가 설계) 반영 방향:

```python
PROMPT_V0 = """
다음은 이번 주 '{topic_title}' 주제로 나눈 대화들입니다.
이 대화들을 바탕으로 따뜻하고 감동적인 수필을 800~1200자로 작성해주세요.

대화 내용:
{conversations}

수필 형식:
- 제목: [제목]
- 본문: (800~1200자)
"""

PROMPT_V1 = """
당신은 한국의 시니어 세대와 청년 세대의 공동 기억을 아름다운 글로 엮는 작가입니다.

이번 주 주제는 '{topic_title}'입니다.
아래는 이 주제로 나눈 실제 대화들입니다.

[대화 모음]
{conversations}

[작성 지침]
1. 대화에서 반복되는 감정과 기억을 중심 주제로 삼으세요
2. 특정인이 특정되지 않도록 익명성을 보호하세요
3. 1인칭 복수("우리")를 활용해 공동체 감각을 살리세요
4. 800~1200자, 현대 한국어 수필체
5. 결말은 현재와 미래를 연결하는 따뜻한 문장으로 마무리

[출력 형식]
제목: <제목>
---
<수필 본문>
"""
```

---

## 모바일 수필 수신 화면

### 현재 상태
- `GET /essay/latest` API: 구현됨
- 모바일 UI: 버튼만 존재, 연결 없음

### ElderlyMain.tsx — "지난 이야기 듣기" 버튼 연결

```typescript
// 상태 추가
const [latestEssay, setLatestEssay] = useState<{
  title: string;
  content: string;
  published_at: string;
  contributor_cnt: number;
} | null>(null);
const [showEssay, setShowEssay] = useState(false);

// 수필 조회 함수
const fetchLatestEssay = async () => {
  try {
    const { data } = await axios.get(`${API}/essay/latest`);
    setLatestEssay(data);
    setShowEssay(true);
    // 수필 내용 읽어드리기
    speakText(`이번 주 수필입니다. 제목: ${data.title}. ${data.content}`);
  } catch (e) {
    speakText("아직 수필이 준비되지 않았어요.");
  }
};

// 버튼에 연결
<TouchableOpacity style={styles.menuBtn} onPress={fetchLatestEssay}>
  <Text style={[styles.menuText, { fontSize: fontSize - 2 }]}>지난 이야기 듣기</Text>
</TouchableOpacity>

// 수필 모달
{showEssay && latestEssay && (
  <View style={styles.essayModal}>
    <TouchableOpacity
      style={styles.closeBtn}
      onPress={() => { setShowEssay(false); Speech.stop(); }}
    >
      <Text style={styles.closeText}>닫기</Text>
    </TouchableOpacity>
    <Text style={[styles.essayTitle, { fontSize: fontSize + 2 }]}>
      {latestEssay.title}
    </Text>
    <Text style={[styles.essayMeta, { fontSize: fontSize - 4 }]}>
      {latestEssay.contributor_cnt}명이 함께 만든 이야기 ·{" "}
      {new Date(latestEssay.published_at).toLocaleDateString("ko-KR")}
    </Text>
    <ScrollView>
      <Text style={[styles.essayContent, { fontSize }]}>
        {latestEssay.content}
      </Text>
    </ScrollView>
  </View>
)}
```

**스타일 추가**:
```typescript
essayModal: {
  position: "absolute", top: 0, left: 0, right: 0, bottom: 0,
  backgroundColor: "#FFFDF7", padding: 24, zIndex: 100,
},
essayTitle: { fontWeight: "bold", color: "#4A3728", marginBottom: 8, marginTop: 48 },
essayMeta: { color: "#AAA", marginBottom: 20 },
essayContent: { color: "#333", lineHeight: 36 },
closeBtn: { position: "absolute", top: 16, right: 16 },
closeText: { color: "#E8572A", fontSize: 16 },
```

---

## 수필 자동 생성 스케줄러 (Phase 2)

Pipeline A의 APScheduler와 연계:

```python
# main.py — 매주 일요일 23:00 수필 자동 생성
async def auto_generate_essay():
    async with AsyncSessionLocal() as db:
        from app.routers.essay import create_essay
        # 간단한 직접 호출 (HTTP 없이)
        try:
            await _do_generate_essay(db)
            logger.info("[Essay] 주간 수필 자동 생성 완료")
        except Exception as e:
            logger.error(f"[Essay] 자동 생성 실패: {e}")

scheduler.add_job(
    auto_generate_essay,
    CronTrigger(day_of_week="sun", hour=23, minute=0),
)
```

---

## 변경 파일 요약

| 파일 | 변경 내용 | 우선순위 |
|---|---|---|
| `backend/app/routers/essay.py` | topic_id 필터 추가, topic_id 저장 | 🔴 즉시 |
| `backend/app/models/models.py` | `EssayContributor` 모델 추가 | 🟡 |
| `backend/app/init.sql` | `essay_contributors` 테이블 추가 | 🟡 |
| `backend/app/services/essay.py` | 프롬프트 v1 추가 | 🟡 |
| `mobile/screens/ElderlyMain.tsx` | 수필 조회/표시 화면 | 🟡 |
| `backend/app/main.py` | 주간 자동 생성 스케줄러 | 🟢 Phase 2 |

---

## 테스트 시나리오

1. **Critical 버그 수정 검증**: topic_id가 다른 두 주제로 각각 5건 대화 후 수필 생성 → 각 수필에 해당 주제 대화만 포함됐는지 확인
2. **Essay.topic_id 저장**: 수필 생성 후 DB `essays.topic_id` NOT NULL 확인
3. **contributor_cnt**: 3명이 각각 2건 대화 → `contributor_cnt = 3` 확인
4. **모바일 수필 화면**: "지난 이야기 듣기" 탭 → 수필 텍스트 표시 및 TTS 재생 확인
5. **빈 대화**: 대화 5건 미만 시 400 오류 반환 확인

---

> **다음 파이프라인**: E — 안전 감지 (1393 연결, APScheduler)
