# Pipeline B — 사용자 대화 상세 구현 계획

> **의존**: Pipeline A (주제 공급)  
> **영향**: C(감정 분석), D(수필 주제 필터링), E(위기 감지)  
> **작성 기준일**: 2026년 6월 1일

---

## 현재 코드 상태 (진단)

| 파일 | 위치 | 문제 |
|---|---|---|
| `mobile/screens/ElderlyMain.tsx` | 10번 줄 | `const API = "http://localhost:8000"` 하드코딩 |
| `mobile/screens/YouthMain.tsx` | 10번 줄 | `const API = "http://localhost:8000"` 하드코딩 |
| `dashboard/src/pages/Dashboard.tsx` | 4번 줄 | `const API = "http://localhost:8000"` 하드코딩 |
| `backend/app/routers/chat.py` | 71번 줄 | `topic_id=None` — 대화에 주제 연결 안 됨 |
| `ElderlyMain.tsx` | 전반 | TTS: `expo-speech` 사용 중, 백엔드 TTS API 미활용 |
| `YouthMain.tsx` | 음악 재생 부분 | `media_url` 없으면 재생 불가, 에러 처리 없음 |

---

## 구현 목표

```
[Bug Fix 1] API URL 환경변수화
            localhost → 환경변수 EXPO_PUBLIC_API_URL

[Bug Fix 2] Conversation.topic_id 실저장
            chat.py topic_id=None → 실제 WeeklyTopic.id 저장

[Feature 1] 음악 재생 (청년용)
            media_url 유효 시 expo-av 스트리밍, 없으면 graceful 처리

[Feature 2] TTS 자동 재생 흐름 완성 (노인용)
            백엔드 TTS API → 음성 재생 or expo-speech 폴백

[Feature 3] 위기 감지 시 1393 팝업 (E 파이프라인 연계)
            [CRISIS] 태그 수신 시 모바일에서 Alert + 전화 연결 버튼
```

---

## Bug Fix 1 — API URL 환경변수화

### 모바일 (Expo)

**파일**: `mobile/package.json` 확인 후 `app.config.js` 또는 `.env` 추가

Expo 환경변수는 `EXPO_PUBLIC_` 접두사 필요.

**새 파일**: `mobile/.env`
```
EXPO_PUBLIC_API_URL=http://192.168.1.100:8000
```

**새 파일**: `mobile/.env.example`
```
EXPO_PUBLIC_API_URL=http://<서버IP>:8000
# 개발: 같은 WiFi의 PC IP 입력 (localhost는 모바일 기기에서 PC를 가리키지 않음)
# 배포: https://api.ium-service.com
```

**수정**: `mobile/screens/ElderlyMain.tsx` 10번 줄
```typescript
// Before
const API = "http://localhost:8000";

// After
const API = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";
```

**수정**: `mobile/screens/YouthMain.tsx` 10번 줄 — 동일하게 수정

### 대시보드 (React/Vite)

**새 파일**: `dashboard/.env`
```
VITE_API_URL=http://localhost:8000
```

**수정**: `dashboard/src/pages/Dashboard.tsx` 4번 줄
```typescript
// Before
const API = "http://localhost:8000";

// After
const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
```

---

## Bug Fix 2 — Conversation.topic_id 실저장

### 백엔드 변경

**파일**: `backend/app/routers/chat.py`

현재 `get_active_topic()`이 dict만 반환 (DB 객체 없음). Pipeline A 완성 후 DB에서 topic.id를 가져올 수 있음.

**수정 전** (71번 줄):
```python
user_conv = Conversation(
    user_id=user.id,
    role="user",
    content=body.message,
    topic_id=None,  # 주제 ID는 DB에 저장된 경우에만
)
```

**수정 후**:
```python
# 이번 주 주제 (db 인수 전달 → DB ID 포함)
topic = await public_data.get_active_topic(db)
topic_uuid = uuid.UUID(topic["id"]) if topic.get("id") else None

user_conv = Conversation(
    user_id=user.id,
    role="user",
    content=body.message,
    topic_id=topic_uuid,
)
```

**AI 응답 저장** (97번 줄) — topic_id 동일하게 저장:
```python
ai_conv = Conversation(
    user_id=user.id,
    role="assistant",
    content=full,
    topic_id=topic_uuid,
)
```

> Pipeline A Step 4 완료 후에야 topic["id"]가 유효해짐.  
> 그 전까지는 `topic_id=None`으로 유지 (현행 유지).

---

## Feature 1 — 청년용 음악 재생

**파일**: `mobile/screens/YouthMain.tsx` 전체 검토

현재 구조 확인 후 media_url 처리 부분 추가:

```typescript
import { Audio } from "expo-av";

// 컴포넌트 상태 추가
const [sound, setSound] = useState<Audio.Sound | null>(null);
const [isPlaying, setIsPlaying] = useState(false);

// 음악 재생 함수
const playMusic = async (mediaUrl: string) => {
  try {
    if (sound) {
      await sound.unloadAsync();
    }
    const { sound: newSound } = await Audio.Sound.createAsync(
      { uri: mediaUrl },
      { shouldPlay: true, isLooping: false }
    );
    setSound(newSound);
    setIsPlaying(true);
    newSound.setOnPlaybackStatusUpdate((status) => {
      if (status.isLoaded && status.didJustFinish) {
        setIsPlaying(false);
      }
    });
  } catch (e) {
    console.warn("음악 재생 실패:", e);
    // 오류 무시 — 음악 없이도 대화 가능
  }
};

const stopMusic = async () => {
  if (sound) {
    await sound.stopAsync();
    setIsPlaying(false);
  }
};

// 주제 로드 시 media_type이 audio이면 자동 재생
useEffect(() => {
  if (topic?.media_url && topic.media_type === "audio") {
    playMusic(topic.media_url);
  }
  return () => {
    sound?.unloadAsync();
  };
}, [topic]);
```

**UI 추가** — 재생/정지 버튼:
```typescript
{topic?.media_url && topic.media_type === "audio" && (
  <TouchableOpacity
    style={styles.musicBtn}
    onPress={isPlaying ? stopMusic : () => playMusic(topic.media_url!)}
  >
    <Text style={styles.musicIcon}>{isPlaying ? "⏸" : "▶"}</Text>
    <Text style={styles.musicLabel}>
      {isPlaying ? "음악 재생 중..." : "배경 음악 듣기"}
    </Text>
  </TouchableOpacity>
)}
```

---

## Feature 2 — 노인용 TTS 완성

### 현재 상태
`ElderlyMain.tsx`는 `expo-speech`(기기 내장 TTS) 사용 중.  
백엔드 `POST /chat/voice/tts` API 구현되어 있으나 모바일에서 미호출.

### 전략: expo-speech 우선, 백엔드 TTS 선택적 적용

Phase 1: expo-speech 현행 유지 (기기 내장, API 없이 작동)  
Phase 2: 고품질 음성이 필요할 때 백엔드 TTS API 호출

**현재 TTS 코드** (`ElderlyMain.tsx:40-47`) — 이미 구현됨:
```typescript
const speakText = (text: string) => {
  setIsSpeaking(true);
  Speech.speak(text, {
    language: "ko-KR",
    rate: 0.85,
    onDone: () => setIsSpeaking(false),
  });
};
```

**개선점**: 위기 응답(`[CRISIS]` 태그) 시 TTS 시작 전 팝업 먼저 표시 (Feature 3에서 처리).

### TTS 자동 재생 흐름 완성

`stopRecordingAndSend()` 함수에서 스트리밍 완료 후 자동 재생 — 이미 구현됨 (89번 줄: `speakText(full)`).

**개선**: 스트리밍 중 청크가 쌓일 때마다 중간 재생하지 않고, 완료 후 한 번에 재생 (현행 유지).

**오류 처리 추가**:
```typescript
const stopRecordingAndSend = async () => {
  setIsRecording(false);
  try {
    await recordingRef.current?.stopAndUnloadAsync();
    const uri = recordingRef.current?.getURI();
    if (!uri) return;

    // STT
    const formData = new FormData();
    formData.append("file", { uri, name: "audio.m4a", type: "audio/m4a" } as any);
    
    let userText: string;
    try {
      const sttRes = await axios.post(`${API}/chat/voice/stt`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 15000,
      });
      userText = sttRes.data.text;
    } catch (sttErr) {
      // STT 실패 시 사용자에게 재시도 안내
      speakText("잘 듣지 못했어요. 다시 말씀해 주시겠어요?");
      return;
    }

    if (!userText?.trim()) {
      speakText("말씀이 들리지 않았어요. 버튼을 누르고 말씀해 주세요.");
      return;
    }

    // AI 응답 스트리밍 ... (기존 코드 유지)
  } catch (err) {
    console.error("대화 오류:", err);
    speakText("잠시 문제가 생겼어요. 조금 후에 다시 시도해 주세요.");
  }
};
```

---

## Feature 3 — 위기 감지 시 1393 팝업

### 백엔드: 이미 구현됨
`claude.py:75-78`: `[CRISIS]` 태그 + 1393 안내 문구 append.

### 모바일: 추가 필요

**파일**: `mobile/screens/ElderlyMain.tsx`

```typescript
import { Alert, Linking } from "react-native";

// 스트리밍 완료 후 위기 감지 처리
const handleAIResponse = (fullResponse: string) => {
  setAiResponse(fullResponse.replace("[CRISIS]", "").trim());
  
  if (fullResponse.startsWith("[CRISIS]")) {
    // TTS 전에 Alert 먼저 표시
    Alert.alert(
      "마음이 많이 힘드신가요?",
      "지금 바로 전문 상담사와 이야기 나눠보시겠어요?\n정신건강 위기상담전화 1393입니다.",
      [
        {
          text: "1393 전화하기",
          onPress: () => Linking.openURL("tel:1393"),
          style: "default",
        },
        {
          text: "괜찮아요",
          style: "cancel",
        },
      ],
      { cancelable: false }
    );
  }
  
  // [CRISIS] 태그 제거 후 TTS
  const cleanResponse = fullResponse.replace(/^\[CRISIS\]\s*/, "");
  speakText(cleanResponse);
};
```

**수정**: `stopRecordingAndSend`의 스트리밍 완료 부분:
```typescript
// 기존:
speakText(full);

// 변경:
handleAIResponse(full);
```

**청년 앱**(`YouthMain.tsx`)도 동일 패턴 적용 (텍스트 대화이므로 Alert만, TTS 없음):
```typescript
const handleCrisis = (response: string) => {
  if (response.startsWith("[CRISIS]")) {
    Alert.alert(
      "힘드신 것 같아요",
      "정신건강 위기상담전화 1393에서 도움을 받을 수 있어요.",
      [
        { text: "1393 전화하기", onPress: () => Linking.openURL("tel:1393") },
        { text: "괜찮아요", style: "cancel" },
      ]
    );
  }
  return response.replace(/^\[CRISIS\]\s*/, "");
};
```

---

## 변경 파일 요약

| 파일 | 변경 내용 | 우선순위 |
|---|---|---|
| `mobile/.env` + `.env.example` | 신규 생성 — API URL 환경변수 | 즉시 |
| `mobile/screens/ElderlyMain.tsx` | API URL 환경변수화, 오류 처리, 위기 팝업 | 즉시 |
| `mobile/screens/YouthMain.tsx` | API URL 환경변수화, 음악 재생, 위기 팝업 | 즉시 |
| `dashboard/.env` + `.env.example` | 신규 생성 — API URL 환경변수 | 즉시 |
| `dashboard/src/pages/Dashboard.tsx` | API URL 환경변수화 | 즉시 |
| `backend/app/routers/chat.py` | topic_id 실저장 (Pipeline A 완성 후) | A 이후 |

---

## 테스트 시나리오

1. **실기기 테스트**: 모바일 기기에서 `EXPO_PUBLIC_API_URL`을 PC의 LAN IP로 설정 후 API 호출 성공 확인
2. **topic_id 저장**: 대화 후 DB에서 `conversations.topic_id` 값이 NULL이 아님 확인
3. **음악 재생**: media_url이 audio인 주제 수동 주입 후 청년 앱에서 자동 재생 확인
4. **위기 팝업**: "죽고 싶"이 포함된 메시지 전송 → Alert 팝업 표시 확인
5. **1393 연결**: Alert에서 "1393 전화하기" 탭 → 기기 전화 앱 열림 확인

---

> **다음 파이프라인**: D — 수필 버그 수정 (topic_id 필터, Critical)
