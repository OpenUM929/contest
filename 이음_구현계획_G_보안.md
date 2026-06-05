# Pipeline G — 데이터 보안 상세 구현 계획

> **의존**: 전 파이프라인 완성 후 횡단 적용  
> **영향**: 모든 파이프라인 (대화 저장/조회 레이어 교체)  
> **작성 기준일**: 2026년 6월 1일

---

## 현재 코드 상태 (진단)

| 파일 | 위치 | 현재 상태 | 문제 |
|---|---|---|---|
| `backend/app/models/models.py` | `Conversation.content` | `Text` 평문 저장 | AES-256 미적용 |
| `backend/app/routers/chat.py` | 전체 | 대화 저장/조회 시 평문 그대로 | 암복호화 레이어 없음 |
| 전체 코드베이스 | — | 비식별화: `is_anonymous` 플래그만 | 대화 내용 비식별화 없음 |
| 모바일 앱 | — | 동의서 UI 없음 | 개인정보 수집 동의 미처리 |
| `backend/app/init.sql` | — | `user_consents` 테이블 없음 | 동의 이력 저장 불가 |

---

## 구현 목표

```
[Step 1] AES-256-GCM 암복호화 유틸
         cryptography 라이브러리 기반

[Step 2] Conversation.content 암복호화 레이어
         저장 시 암호화 / 조회 시 복호화 (투명하게)

[Step 3] 비식별화 처리
         분석/보고 시 user_id → 랜덤 코드

[Step 4] 동의서 UI (모바일)
         회원가입 시 개인정보 수집 동의

[Step 5] user_consents 테이블
         동의 이력 DB 저장
```

---

## Step 1 — AES-256-GCM 암복호화 유틸

### 의존성 추가

`requirements.txt`:
```
cryptography==42.0.8
```

### 암호화 키 설정

**파일**: `backend/app/config.py`

```python
# AES-256 키: 32바이트 (256비트) base64 인코딩
# python -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
ENCRYPTION_KEY: str = ""  # 운영 환경에서 반드시 설정
```

**`.env.example` 추가**:
```
# AES-256 암호화 키 (base64 인코딩된 32바이트)
# 생성: python -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
ENCRYPTION_KEY=<your_32_byte_base64_key_here>
```

### 암복호화 유틸

**새 파일**: `backend/app/services/encryption.py`

```python
import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.config import settings

_KEY: bytes | None = None


def _get_key() -> bytes:
    global _KEY
    if _KEY is None:
        if not settings.encryption_key:
            # 개발 환경: 임시 키 사용 (경고 출력)
            import logging
            logging.getLogger("ium.security").warning(
                "[Security] ENCRYPTION_KEY 미설정. 임시 키 사용 (개발 전용)"
            )
            # 재시작 시 데이터 복호화 불가 — 개발 환경에서만 허용
            _KEY = os.urandom(32)
        else:
            _KEY = base64.b64decode(settings.encryption_key)
            if len(_KEY) != 32:
                raise ValueError("ENCRYPTION_KEY는 32바이트(256비트)여야 합니다")
    return _KEY


def encrypt(plaintext: str) -> str:
    """
    AES-256-GCM 암호화.
    반환값: base64(nonce + ciphertext + tag) — DB 저장용
    """
    if not plaintext:
        return plaintext
    
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # GCM 권장 96비트 nonce
    
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    
    # nonce(12) + ciphertext+tag 를 base64로 저장
    return base64.b64encode(nonce + ciphertext).decode("ascii")


def decrypt(ciphertext_b64: str) -> str:
    """
    AES-256-GCM 복호화.
    입력: base64(nonce + ciphertext + tag)
    """
    if not ciphertext_b64:
        return ciphertext_b64
    
    # 평문이 저장된 경우 (마이그레이션 전 데이터) 그대로 반환
    try:
        raw = base64.b64decode(ciphertext_b64)
    except Exception:
        return ciphertext_b64  # base64 디코딩 실패 = 평문
    
    if len(raw) < 28:  # nonce(12) + 최소 tag(16) 
        return ciphertext_b64  # 형식 불일치 = 평문 처리
    
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = raw[:12]
    ciphertext = raw[12:]
    
    try:
        return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")
    except Exception:
        # 복호화 실패 (키 변경 등) → 원문 반환 (로그 기록)
        import logging
        logging.getLogger("ium.security").error("[Security] 복호화 실패 — 평문 반환")
        return "[복호화 실패]"


def is_encrypted(value: str) -> bool:
    """저장된 값이 암호화된 것인지 판별 (마이그레이션 시 유용)"""
    try:
        raw = base64.b64decode(value)
        return len(raw) >= 28
    except Exception:
        return False
```

---

## Step 2 — Conversation.content 암복호화 레이어

### 방식: SQLAlchemy TypeDecorator

DB 저장 시 자동 암호화, 조회 시 자동 복호화. 코드 변경 최소화.

**파일**: `backend/app/models/models.py`

```python
from sqlalchemy import TypeDecorator
from app.services.encryption import encrypt, decrypt

class EncryptedText(TypeDecorator):
    """DB에 AES-256-GCM으로 암호화하여 저장하는 컬럼 타입"""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Python → DB: 암호화"""
        if value is not None:
            return encrypt(value)
        return value

    def process_result_value(self, value, dialect):
        """DB → Python: 복호화"""
        if value is not None:
            return decrypt(value)
        return value
```

**Conversation 모델 수정**:
```python
class Conversation(Base):
    ...
    # 변경: Text → EncryptedText
    content: Mapped[str] = mapped_column(EncryptedText)
    ...
```

> **주의**: 이 변경 적용 후에는 기존 평문 데이터가 복호화 실패할 수 있음.  
> 마이그레이션 스크립트 실행 필요 (아래 Step 2-2).

### 2-2. 기존 데이터 마이그레이션 스크립트

**새 파일**: `backend/scripts/migrate_encrypt_conversations.py`

```python
"""
기존 평문 Conversation.content를 AES-256으로 암호화.
최초 1회 실행 후 제거.
"""
import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal
from app.services.encryption import encrypt, is_encrypted

async def migrate():
    async with AsyncSessionLocal() as db:
        # 전체 대화 조회 (raw SQL로 암호화 레이어 우회)
        result = await db.execute(
            text("SELECT id, content FROM conversations")
        )
        rows = result.fetchall()
        
        migrated = 0
        for row in rows:
            conv_id, content = row
            if content and not is_encrypted(content):
                encrypted = encrypt(content)
                await db.execute(
                    text("UPDATE conversations SET content = :enc WHERE id = :id"),
                    {"enc": encrypted, "id": str(conv_id)},
                )
                migrated += 1
        
        await db.commit()
        print(f"마이그레이션 완료: {migrated}/{len(rows)}건 암호화")

if __name__ == "__main__":
    asyncio.run(migrate())
```

---

## Step 3 — 비식별화 처리

### 복지사 대시보드 보고 API

분석/보고 시 `user_id` → 랜덤 코드로 치환:

```python
import hashlib

def anonymize_user_id(user_id: str, salt: str = "ium_anon_salt") -> str:
    """user_id를 복원 불가능한 8자리 코드로 치환"""
    return hashlib.sha256(f"{salt}:{user_id}".encode()).hexdigest()[:8].upper()
```

**API 추가**: `GET /welfare/report/anonymized`

```python
@router.get("/report/anonymized", summary="비식별화 통계 보고")
async def get_anonymized_report(db: AsyncSession = Depends(get_db)):
    """지역별 집계 — user_id 비식별화 적용"""
    result = await db.execute(
        select(Conversation.user_id, Conversation.emotion_label, Conversation.created_at)
        .where(Conversation.role == "user")
        .order_by(Conversation.created_at.desc())
        .limit(1000)
    )
    rows = result.all()
    
    return {
        "records": [
            {
                "anon_id": anonymize_user_id(str(r.user_id)),
                "emotion": r.emotion_label,
                "date": r.created_at.date().isoformat(),
            }
            for r in rows
        ],
        "total": len(rows),
        "note": "user_id는 복원 불가능한 코드로 치환되었습니다.",
    }
```

---

## Step 4 — 동의서 UI (모바일)

### 회원가입 플로우 설계

```
[앱 최초 실행]
    ↓
[개인정보 동의 화면]
수집 항목: 음성 대화 내용, 감정 분석 결과
이용 목적: AI 동반자 서비스, 복지사 안전 모니터링
보유 기간: 서비스 탈퇴 시까지
    ↓
[동의/거부] ← 거부 시 서비스 이용 불가 안내
    ↓
[닉네임 입력] → [회원가입 완료]
```

### 새 화면: `mobile/screens/ConsentScreen.tsx`

```typescript
import React, { useState } from "react";
import {
  View, Text, ScrollView, TouchableOpacity,
  StyleSheet, Alert,
} from "react-native";
import axios from "axios";

const API = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

const CONSENT_ITEMS = [
  {
    id: "service",
    title: "서비스 이용 약관 (필수)",
    content: `이음(以音) 서비스를 이용하기 위한 약관입니다.
    
1. 서비스 목적: AI 동반자와의 대화를 통해 정서적 지지 제공
2. 서비스 운영: 수집된 대화 내용을 AI 분석에 활용
3. 이용 제한: 만 60세 이상 또는 복지관 지정 청년`,
  },
  {
    id: "privacy",
    title: "개인정보 수집·이용 동의 (필수)",
    content: `수집 항목: 음성/텍스트 대화 내용, 감정 분석 결과, 접속 일시
이용 목적: AI 동반자 서비스, 복지사 안전 모니터링, 서비스 개선
보유 기간: 회원 탈퇴 시까지 (단, 법령에 따라 보존 필요한 경우 제외)
제3자 제공: 담당 복지사에게 안전 이상 시 알림 제공 (이름/연락처 비공개)`,
  },
  {
    id: "sensitive",
    title: "민감정보(정서·심리 상태) 처리 동의 (필수)",
    content: `AI 대화 분석을 통해 감정 상태(긍정/부정/중립)를 수집합니다.
이는 자살위기 등 안전 상황 감지를 위한 목적으로만 사용됩니다.
수집된 심리 지표는 암호화 저장되며 담당 복지사에게 요약 형태로만 제공됩니다.`,
  },
];

export default function ConsentScreen({
  onComplete,
}: {
  onComplete: (userId: string) => void;
}) {
  const [agreed, setAgreed] = useState<Record<string, boolean>>({});
  const [expanded, setExpanded] = useState<string | null>(null);
  const [nickname, setNickname] = useState("");
  const [userType, setUserType] = useState<"elder" | "youth">("elder");

  const allRequired = CONSENT_ITEMS.filter(
    (i) => i.id !== "optional"
  ).every((i) => agreed[i.id]);

  const handleSubmit = async () => {
    if (!allRequired) {
      Alert.alert("필수 동의 항목을 모두 확인해 주세요.");
      return;
    }
    if (!nickname.trim()) {
      Alert.alert("닉네임을 입력해 주세요.");
      return;
    }

    try {
      // 사용자 등록
      const { data: user } = await axios.post(`${API}/chat/users`, {
        user_type: userType,
        nickname: nickname.trim(),
      });

      // 동의 이력 저장
      await axios.post(`${API}/auth/consent`, {
        user_id: user.user_id,
        consented_items: Object.keys(agreed).filter((k) => agreed[k]),
      });

      onComplete(user.user_id);
    } catch (e) {
      Alert.alert("가입 중 오류가 발생했습니다. 다시 시도해 주세요.");
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>이음(以音) 서비스 동의</Text>
      <Text style={styles.subtitle}>서비스 이용 전 아래 내용을 확인해 주세요.</Text>

      {CONSENT_ITEMS.map((item) => (
        <View key={item.id} style={styles.consentItem}>
          <TouchableOpacity
            style={styles.consentHeader}
            onPress={() => setExpanded(expanded === item.id ? null : item.id)}
          >
            <TouchableOpacity
              style={[styles.checkbox, agreed[item.id] && styles.checked]}
              onPress={() => setAgreed((a) => ({ ...a, [item.id]: !a[item.id] }))}
            >
              {agreed[item.id] && <Text style={styles.checkmark}>✓</Text>}
            </TouchableOpacity>
            <Text style={styles.consentTitle}>{item.title}</Text>
            <Text style={styles.expandIcon}>{expanded === item.id ? "▲" : "▼"}</Text>
          </TouchableOpacity>
          {expanded === item.id && (
            <Text style={styles.consentContent}>{item.content}</Text>
          )}
        </View>
      ))}

      {/* 닉네임 입력 */}
      <View style={styles.nicknameSection}>
        <Text style={styles.label}>사용할 이름 (닉네임)</Text>
        {/* TextInput 추가 필요 */}
      </View>

      <TouchableOpacity
        style={[styles.submitBtn, !allRequired && styles.submitDisabled]}
        onPress={handleSubmit}
        disabled={!allRequired}
      >
        <Text style={styles.submitText}>동의하고 시작하기</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#FFFDF7", padding: 24 },
  title: { fontSize: 24, fontWeight: "bold", color: "#4A3728", marginBottom: 8 },
  subtitle: { fontSize: 14, color: "#888", marginBottom: 24 },
  consentItem: { marginBottom: 12, borderRadius: 12, backgroundColor: "#F5F0E8", overflow: "hidden" },
  consentHeader: { flexDirection: "row", alignItems: "center", padding: 16, gap: 12 },
  checkbox: {
    width: 24, height: 24, borderRadius: 4, borderWidth: 2,
    borderColor: "#CCC", justifyContent: "center", alignItems: "center",
  },
  checked: { backgroundColor: "#E8572A", borderColor: "#E8572A" },
  checkmark: { color: "#FFF", fontSize: 14, fontWeight: "bold" },
  consentTitle: { flex: 1, fontSize: 15, color: "#333" },
  expandIcon: { color: "#888", fontSize: 12 },
  consentContent: { padding: 16, paddingTop: 0, fontSize: 13, color: "#555", lineHeight: 22 },
  nicknameSection: { marginVertical: 20 },
  label: { fontSize: 16, color: "#333", marginBottom: 8 },
  submitBtn: {
    backgroundColor: "#E8572A", borderRadius: 12, padding: 18,
    alignItems: "center", marginBottom: 48,
  },
  submitDisabled: { backgroundColor: "#CCC" },
  submitText: { color: "#FFF", fontSize: 18, fontWeight: "bold" },
});
```

---

## Step 5 — user_consents 테이블

### 모델 추가

**파일**: `backend/app/models/models.py`

```python
class UserConsent(Base):
    __tablename__ = "user_consents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    consent_type: Mapped[str] = mapped_column(String(50))   # service | privacy | sensitive | optional
    agreed: Mapped[bool] = mapped_column(Boolean, default=True)
    agreed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ip_address: Mapped[str | None] = mapped_column(String(50))
    app_version: Mapped[str | None] = mapped_column(String(20))
```

**init.sql 추가**:
```sql
CREATE TABLE IF NOT EXISTS user_consents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    consent_type VARCHAR(50) NOT NULL,
    agreed BOOLEAN DEFAULT TRUE,
    agreed_at TIMESTAMP DEFAULT NOW(),
    ip_address VARCHAR(50),
    app_version VARCHAR(20)
);
CREATE INDEX ON user_consents (user_id);
```

### API 추가

**새 router**: `backend/app/routers/auth.py`

```python
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database import get_db
from app.models.models import UserConsent
import uuid

router = APIRouter(prefix="/auth", tags=["auth"])


class ConsentCreate(BaseModel):
    user_id: str
    consented_items: list[str]   # ["service", "privacy", "sensitive"]
    app_version: str | None = None


@router.post("/consent", summary="동의 이력 저장")
async def save_consent(
    body: ConsentCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    client_ip = request.client.host if request.client else None
    user_uuid = uuid.UUID(body.user_id)
    
    for consent_type in ["service", "privacy", "sensitive", "optional"]:
        consent = UserConsent(
            user_id=user_uuid,
            consent_type=consent_type,
            agreed=(consent_type in body.consented_items),
            ip_address=client_ip,
            app_version=body.app_version,
        )
        db.add(consent)
    
    await db.commit()
    return {"status": "saved", "count": 4}


@router.get("/consent/{user_id}", summary="동의 이력 조회")
async def get_consent(user_id: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    result = await db.execute(
        select(UserConsent)
        .where(UserConsent.user_id == uuid.UUID(user_id))
        .order_by(UserConsent.agreed_at.desc())
    )
    consents = result.scalars().all()
    return [
        {
            "type": c.consent_type,
            "agreed": c.agreed,
            "date": c.agreed_at.isoformat(),
        }
        for c in consents
    ]
```

**main.py 라우터 등록 추가**:
```python
from app.routers import auth
app.include_router(auth.router)
```

---

## 보안 체크리스트

| 항목 | 상태 후 | 비고 |
|---|---|---|
| 대화 내용 암호화 | ✅ AES-256-GCM | TypeDecorator 투명 적용 |
| 복호화 키 관리 | ✅ 환경변수 | 코드에 키 하드코딩 금지 |
| 비식별화 | ✅ SHA-256 해시 | 보고서 API 한정 |
| 동의서 UI | ✅ 3개 필수 항목 | 거부 시 서비스 이용 불가 |
| 동의 이력 저장 | ✅ DB + IP + 버전 | 법적 증빙용 |
| HTTPS | ⚠️ 배포 시 필수 | Nginx reverse proxy 설정 필요 |
| SQL Injection | ✅ SQLAlchemy ORM | raw SQL 최소화 |
| 세션 관리 | ⚠️ 미구현 | 현재 user_id만 사용, JWT 도입 검토 |

---

## 변경 파일 요약

| 파일 | 변경 내용 | 우선순위 |
|---|---|---|
| `backend/app/services/encryption.py` | 신규 — AES-256-GCM 유틸 | 🟡 |
| `backend/app/models/models.py` | `EncryptedText` TypeDecorator, `UserConsent`, `Conversation.content` 타입 변경 | 🟡 |
| `backend/app/init.sql` | `user_consents` 테이블 추가 | 🟡 |
| `backend/app/config.py` | `ENCRYPTION_KEY` 추가 | 🟡 |
| `backend/app/routers/auth.py` | 신규 — 동의 저장/조회 API | 🟡 |
| `backend/app/main.py` | `auth` 라우터 등록 | 🟡 |
| `mobile/screens/ConsentScreen.tsx` | 신규 — 동의서 UI | 🟡 |
| `backend/scripts/migrate_encrypt_conversations.py` | 신규 — 기존 데이터 마이그레이션 | 🟡 |

---

## 테스트 시나리오

1. **암호화 저장**: 대화 후 DB `conversations.content` 컬럼이 base64 암호문인지 확인
2. **복호화 조회**: `/chat/message` 스트리밍 응답이 사람이 읽을 수 있는 텍스트인지 확인
3. **키 변경 대응**: ENCRYPTION_KEY 변경 후 기존 데이터 조회 → "[복호화 실패]" 로그 출력, 서비스 중단 없음
4. **동의서 UI**: ConsentScreen에서 필수 3개 미동의 시 "시작하기" 버튼 비활성화 확인
5. **동의 이력**: 동의 후 `GET /auth/consent/{user_id}` → 3개 레코드 반환 확인
6. **비식별화**: `GET /welfare/report/anonymized` → user_id 대신 8자리 코드 반환 확인
7. **마이그레이션**: `migrate_encrypt_conversations.py` 실행 전후 대화 내용 암호화 확인

---

> **전체 완성 후 최종 검토**: 전 파이프라인 통합 테스트 및 보안 취약점 점검
