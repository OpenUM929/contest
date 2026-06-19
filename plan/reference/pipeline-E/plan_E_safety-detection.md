# Pipeline E — 안전 감지 · 긴급 대응 상세 구현 계획

> **의존**: Pipeline B (대화 저장), Pipeline C (감정 분석)  
> **영향**: Pipeline F (복지사 알림)  
> **작성 기준일**: 2026년 6월 1일

---

## 현재 코드 상태 (진단)

| 파일 | 위치 | 현재 상태 | 문제 |
|---|---|---|---|
| `backend/app/services/claude.py` | 75~78번 줄 | `[CRISIS]` 태그 + 1393 텍스트 삽입 | 앱에서 자동 전화 연결 없음 |
| `backend/app/services/alert.py` | 36번 줄 | `logger.warning` + `# TODO Phase 2` | 복지사에게 실제 알림 미전송 |
| `backend/app/routers/safety.py` | 전체 | 수동 API 조회만 가능 | 자동 일괄 점검(스케줄러) 없음 |
| `backend/app/main.py` | 전체 | APScheduler 없음 | 정기 안전 점검 불가 |
| `mobile/screens/ElderlyMain.tsx` | 전체 | 위기 팝업 없음 | 사용자가 직접 전화해야 함 |

---

## 구현 목표

```
[Trigger 1] 위기 키워드 감지 (실시간)
chat.py 대화 중 detect_crisis_level() 실행
    ├─ high → 모바일 Alert 팝업 (1393 전화 버튼) + 복지사 즉시 이메일
    ├─ medium → 1393 텍스트 안내 + 복지사 이메일 (1시간 이내)
    └─ low → DB 기록만

[Trigger 2] 접속 단절 감지 (스케줄)
APScheduler 매일 09:00 → check_no_contact() 전체 사용자
    3일 이상 미접속 → 복지사 이메일 + 앱 푸시

[Trigger 3] 감정 악화 감지 (스케줄)
APScheduler 매일 실행 → check_emotion_trend() 전체 사용자
    red → 복지사 즉시 이메일
    yellow → 복지사 요약 이메일 (일 1회)
```

---

## Step 1 — 이메일 발송 구현

### 1-1. 의존성 추가

`requirements.txt`:
```
aiosmtplib==3.0.1
jinja2==3.1.4
```

### 1-2. 이메일 설정

**파일**: `backend/app/config.py`

```python
# 추가 환경변수
SMTP_HOST: str = "smtp.gmail.com"
SMTP_PORT: int = 587
SMTP_USER: str = ""          # Gmail 주소
SMTP_PASSWORD: str = ""      # Gmail App Password (2단계 인증 후 발급)
WELFARE_NOTIFY_EMAIL: str = ""  # 복지사 이메일 (기본값)
SENDGRID_API_KEY: str = ""   # SendGrid 사용 시 대안
```

**`.env.example` 추가**:
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=ium-service@gmail.com
SMTP_PASSWORD=your_app_password_here
WELFARE_NOTIFY_EMAIL=welfare@example.com
```

### 1-3. 이메일 유틸

**새 파일**: `backend/app/services/email_service.py`

```python
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from app.config import settings

logger = logging.getLogger("ium.email")


async def send_alert_email(
    to_email: str,
    subject: str,
    body_html: str,
) -> bool:
    """HTML 이메일 발송. 실패 시 False 반환 (서비스 중단 없음)"""
    if not settings.smtp_user or not settings.smtp_password:
        logger.warning("[Email] SMTP 설정 없음, 이메일 발송 스킵")
        return False
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"이음 안전알림 <{settings.smtp_user}>"
    msg["To"] = to_email
    msg.attach(MIMEText(body_html, "html", "utf-8"))
    
    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            start_tls=True,
        )
        logger.info(f"[Email] 발송 성공: {to_email} / {subject}")
        return True
    except Exception as e:
        logger.error(f"[Email] 발송 실패: {e}")
        return False


# 이메일 템플릿

def build_crisis_email(nickname: str, crisis_level: str, message_excerpt: str) -> tuple[str, str]:
    """위기 상황 이메일 제목 + 본문"""
    level_label = {"high": "⚠️ 긴급", "medium": "🟡 주의", "low": "ℹ️ 참고"}.get(crisis_level, "알림")
    subject = f"[이음] {level_label} 알림 — {nickname}님 위기 키워드 감지"
    body = f"""
    <html><body style="font-family: sans-serif; padding: 24px;">
    <h2 style="color: {'#CC0000' if crisis_level == 'high' else '#FFA500'}">
        {level_label}: {nickname}님 위기 상황 감지
    </h2>
    <p>이음 AI 대화 중 위기 관련 표현이 감지되었습니다.</p>
    <table style="border-collapse: collapse; width: 100%;">
        <tr><td style="padding: 8px; font-weight: bold;">담당 이용자</td><td>{nickname}</td></tr>
        <tr><td style="padding: 8px; font-weight: bold;">감지 수준</td><td>{crisis_level.upper()}</td></tr>
        <tr><td style="padding: 8px; font-weight: bold;">감지 내용</td><td>"{message_excerpt}"</td></tr>
    </table>
    <p style="margin-top: 24px; color: #666;">
        이음 복지사 대시보드에서 상세 확인 후 필요 시 연락해 주세요.
    </p>
    </body></html>
    """
    return subject, body


def build_no_contact_email(nickname: str, days_absent: int) -> tuple[str, str]:
    subject = f"[이음] 🔴 미접속 알림 — {nickname}님 {days_absent}일째 접속 없음"
    body = f"""
    <html><body style="font-family: sans-serif; padding: 24px;">
    <h2 style="color: #CC0000">미접속 알림: {nickname}님</h2>
    <p>{nickname}님이 <strong>{days_absent}일째</strong> 이음에 접속하지 않고 있습니다.</p>
    <p>안부 확인 또는 방문 서비스가 필요할 수 있습니다.</p>
    </body></html>
    """
    return subject, body


def build_emotion_drop_email(nickname: str, severity: str, stats: dict) -> tuple[str, str]:
    icon = "🔴" if severity == "red" else "🟡"
    subject = f"[이음] {icon} 감정 하락 알림 — {nickname}님 부정 감정 지속"
    body = f"""
    <html><body style="font-family: sans-serif; padding: 24px;">
    <h2 style="color: {'#CC0000' if severity == 'red' else '#FFA500'}">
        감정 하락 감지: {nickname}님
    </h2>
    <p>최근 {stats.get('days', 7)}일간 부정 감정이 지속되고 있습니다.</p>
    <ul>
        <li>부정 감정 횟수: {stats.get('neg_count', '?')}회</li>
        <li>마지막 3회 연속 부정: {'예' if stats.get('last_three_neg') else '아니오'}</li>
    </ul>
    </body></html>
    """
    return subject, body
```

---

## Step 2 — alert.py 이메일 연동

**파일**: `backend/app/services/alert.py`

`trigger_alert()` 수정:

```python
async def trigger_alert(
    db: AsyncSession,
    user_id: str,
    alert_type: str,
    severity: str,
    note: str = "",
    crisis_level: str | None = None,
    message_excerpt: str = "",
) -> SafetyAlert:
    # DB 저장 (기존 유지)
    alert = SafetyAlert(
        user_id=user_id,
        alert_type=alert_type,
        severity=severity,
        note=note,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    logger.warning(
        "[ALERT] user=%s type=%s severity=%s note=%s",
        user_id, alert_type, severity, note,
    )
    
    # 복지사 이메일 주소 조회
    user_result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )
    user = user_result.scalar_one_or_none()
    
    welfare_email = None
    if user and user.welfare_id:
        wf_result = await db.execute(
            select(WelfareWorker).where(WelfareWorker.id == user.welfare_id)
        )
        wf = wf_result.scalar_one_or_none()
        welfare_email = wf.email if wf else None
    
    # 폴백: 기본 복지사 이메일 (설정값)
    welfare_email = welfare_email or settings.welfare_notify_email
    
    if welfare_email:
        from app.services.email_service import (
            send_alert_email, build_crisis_email,
            build_no_contact_email, build_emotion_drop_email
        )
        
        nickname = user.nickname if user else "이용자"
        
        if alert_type == "crisis" and crisis_level:
            subject, body = build_crisis_email(nickname, crisis_level, message_excerpt)
        elif alert_type == "no_contact":
            days = int(note.replace("일 이상 미접속", "").strip()) if "일" in note else 3
            subject, body = build_no_contact_email(nickname, days)
        elif alert_type == "emotion_drop":
            subject, body = build_emotion_drop_email(nickname, severity, {})
        else:
            subject = f"[이음] 알림: {nickname}님 {alert_type}"
            body = f"<p>{note}</p>"
        
        # 비동기 발송 (실패해도 서비스 중단 없음)
        asyncio.create_task(send_alert_email(welfare_email, subject, body))
    
    return alert
```

**chat.py 수정** — trigger_alert 호출 시 추가 정보 전달:

```python
if crisis_level:
    await alert.trigger_alert(
        db, str(user.id), "crisis",
        "red" if crisis_level == "high" else "yellow",
        note=f"키워드 감지: {crisis_level}",
        crisis_level=crisis_level,
        message_excerpt=body.message[:50],  # 최대 50자
    )
```

---

## Step 3 — APScheduler 자동 안전 점검

**파일**: `backend/app/main.py` (Pipeline A의 scheduler에 job 추가)

```python
async def daily_safety_check():
    """매일 09:00 — 전체 사용자 안전 점검"""
    from app.services.alert import check_no_contact, get_recent_emotions, trigger_alert
    from app.services.emotion import check_emotion_trend
    
    async with AsyncSessionLocal() as db:
        # 모든 elder 사용자 조회
        result = await db.execute(
            select(User).where(User.user_type == "elder")
        )
        users = result.scalars().all()
        
        for user in users:
            user_id_str = str(user.id)
            
            # 1. 접속 단절 확인
            if await check_no_contact(db, user_id_str):
                from datetime import datetime, timedelta
                last_seen = user.last_seen_at
                days_absent = (datetime.utcnow() - last_seen).days if last_seen else 30
                await trigger_alert(
                    db, user_id_str, "no_contact", "yellow",
                    note=f"{days_absent}일 이상 미접속",
                )
            
            # 2. 감정 악화 추세 확인
            recent = await get_recent_emotions(db, user_id_str, days=7)
            trend_level = await check_emotion_trend(recent)
            if trend_level:
                neg_count = sum(1 for e in recent if e["label"] == "negative")
                last_three_neg = all(e["label"] == "negative" for e in recent[-3:]) if len(recent) >= 3 else False
                await trigger_alert(
                    db, user_id_str, "emotion_drop", trend_level,
                    note=f"최근 7일 부정 {neg_count}회",
                )
        
        logger.info(f"[SafetyCheck] {len(users)}명 안전 점검 완료")


# scheduler.add_job 추가
scheduler.add_job(
    daily_safety_check,
    CronTrigger(hour=9, minute=0, timezone="Asia/Seoul"),
)
```

---

## Step 4 — 심각도별 대응 프로토콜 분기

### 현재 `detect_crisis_level()` → `chat.py` 분기 강화

**파일**: `backend/app/routers/chat.py`

```python
crisis_level = claude.detect_crisis_level(body.message)
if crisis_level:
    # severity 매핑
    severity_map = {"high": "red", "medium": "yellow", "low": "yellow"}
    severity = severity_map.get(crisis_level, "yellow")
    
    await alert.trigger_alert(
        db, str(user.id), "crisis", severity,
        note=f"키워드 감지: {crisis_level}",
        crisis_level=crisis_level,
        message_excerpt=body.message[:50],
    )
    
    # high 수준: 즉시 알림 (이미 trigger_alert에서 처리)
    # medium/low: trigger_alert가 이메일 발송
```

### 모바일 위기 팝업 (Pipeline B Feature 3에서 이미 정의)

`ElderlyMain.tsx`, `YouthMain.tsx`에서 `[CRISIS]` 태그 수신 시:
- **high**: Alert + "지금 바로 1393 전화하기" 버튼
- **medium/low**: 텍스트 안내 (팝업 없음)

문제: 백엔드에서 crisis_level을 모바일로 전달하는 채널 없음.  
현재 스트리밍 응답에 `[CRISIS]` 태그만 포함됨.

**해결**: 스트리밍 응답 헤더 또는 첫 번째 청크에 레벨 정보 포함:

```python
# claude.py stream_chat 수정
if crisis_level == "high":
    yield "[CRISIS:HIGH]"
elif crisis_level in ("medium", "low"):
    yield "[CRISIS:LOW]"
```

모바일에서:
```typescript
if (full.includes("[CRISIS:HIGH]")) {
  // 즉시 전화 Alert
  Alert.alert("긴급", "1393 전화하기", [...])
} else if (full.includes("[CRISIS:LOW]")) {
  // 텍스트 안내만
}
const cleanResponse = full.replace(/\[CRISIS:[A-Z]+\]\s*/g, "");
```

---

## Step 5 — 안전 점검 API 개선

**파일**: `backend/app/routers/safety.py`

### 전체 사용자 일괄 점검 API (관리자/스케줄러용)

```python
@router.post("/check-all", summary="전체 사용자 안전 점검 (관리자)")
async def check_all_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.user_type == "elder")
    )
    users = result.scalars().all()
    
    triggered = []
    for user in users:
        user_id = str(user.id)
        no_contact = await check_no_contact(db, user_id)
        recent = await get_recent_emotions(db, user_id, days=7)
        trend = await check_emotion_trend(recent)
        
        if no_contact:
            await trigger_alert(db, user_id, "no_contact", "yellow", "3일 이상 미접속")
            triggered.append({"user_id": user_id, "type": "no_contact"})
        if trend:
            await trigger_alert(db, user_id, "emotion_drop", trend, "감정 하락")
            triggered.append({"user_id": user_id, "type": "emotion_drop", "level": trend})
    
    return {"checked": len(users), "triggered": len(triggered), "details": triggered}
```

---

## 변경 파일 요약

| 파일 | 변경 내용 | 우선순위 |
|---|---|---|
| `backend/app/services/email_service.py` | 신규 — SMTP 이메일 발송 유틸 | 🔴 |
| `backend/app/services/alert.py` | 이메일 발송 연동, trigger_alert 확장 | 🔴 |
| `backend/app/routers/chat.py` | crisis_level 정보 확장 전달 | 🟡 |
| `backend/app/services/claude.py` | `[CRISIS:HIGH]`/`[CRISIS:LOW]` 태그 수정 | 🟡 |
| `mobile/screens/ElderlyMain.tsx` | CRISIS 수준별 팝업 분기 | 🟡 |
| `mobile/screens/YouthMain.tsx` | CRISIS 팝업 추가 | 🟡 |
| `backend/app/main.py` | `daily_safety_check` APScheduler job 추가 | 🔴 |
| `backend/app/routers/safety.py` | `/check-all` API 추가 | 🟡 |
| `backend/app/config.py` | SMTP 관련 환경변수 추가 | 🔴 |
| `requirements.txt` | `aiosmtplib`, `jinja2` 추가 | 🔴 |

---

## 테스트 시나리오

1. **위기 키워드 이메일**: "죽고 싶어요" 메시지 전송 → 복지사 이메일 수신 확인 (Gmail 발신 테스트)
2. **미접속 감지**: `last_seen_at`을 4일 전으로 수동 수정 → `/safety/check/{user_id}` 호출 → 이메일 발송
3. **감정 악화 이메일**: 최근 7일 부정 감정 5회 이상 → 이메일 수신 확인
4. **스케줄러 즉시 실행**: `/admin/safety/check-all` 호출 → 전체 점검 결과 반환
5. **SMTP 실패**: SMTP 설정 없을 때 → 서비스 중단 없이 경고 로그만 출력

---

> **다음 파이프라인**: F — 복지사 알림 (resolveAlert 수정, 위험도 복합 조건)
