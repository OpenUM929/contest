# 답변 및 작업 지침

## 1. 핵심 원칙

### 1.1 답변 원칙
- **먼저 직접 확인/분석**してから결론을 제시
- 여러 선택지를 묻지말것. 단일 플랜 1개만 제안
- "어떤 방향으로 진행할까요?" 금지

### 1.2 확인 방법
```
1. 검색 (websearch) - 실시간 정보
2. 파일 확인 (read) - 현재 상태
3. 실행 (bash) - 시스템 상태
4. 추론 - 결과 바탕으로 분석
```

### 1.3 작업 원칙
- 플랜 모드일 경우 먼저 확인/분석
- 코드는 직접 수정 (Write/Edit 도구 사용 가능)
- 파일 수정 전 반드시 기존 코드 Read 필수

---

## 2. LLM API 연동 시 핵심 흐름

### 2.1 구조 (중요!)
```
사용자 (Flask:5000)
    ↓ 요청
Flask 서버
    ↓ LLM 호출
LLM API 서버 (gemini/openrouter/opencode 등)
    ↓
AI 모델
    ↓ 답변
LLM API 서버
    ↓
Flask 서버
    ↓
사용자
```

### 2.2 KEY 확인 우선순위
1. **.env 파일 확인** - 이미 설정된 KEY가 어떤 provider인지 확인
2. **검색으로 특징 파악** - KEY 포맷으로 provider 추정
3. **model 정보 확인** - 어떤 모델이 무료인지 검색

### 2.3 .env KEY 종류
| KEY | Provider | 모델 |
|-----|----------|------|
| GEMINI_API_KEY | Google Gemini | gemini-2.0-flash 등 |
| OPENROUTER_API_KEY | OpenRouter | 300+ 모델 (일부 무료) |
| OPENCODE_API_KEY | OpenCode Zen | **big-pickle** (무료) |

---

## 3. OpenCode Big Pickle 연동 (현재 프로젝트용)

### 3.1 현재 상태
- Flask 서버: 포트 5000
- .env에 OPENCODE_API_KEY 있음 (sk-5DWC...开头)
- LLM: big-pickle 사용 필요

### 3.2 설정
```python
# nlp_pipeline.py의 create_opencode_client()
base_url = "https://opencode.ai/zen/v1"  # OPENCODE Zen 서버
model = "big-pickle"  # 무료 모델
api_key = os.getenv("OPENCODE_API_KEY")  # .env의 KEY 사용
```

### 3.3 중요: opencode/zen vs localhost
| 구분 | base_url | 설명 |
|------|---------|------|
| **OpenCode Zen** | https://opencode.ai/zen/v1 | 클라우드, 무료모델 (big-pickle) |
| **OpenCode 로컬** | http://localhost:4096/v1 | 별도 서버 실행 필요 |

---

## 4. 실수避免 방법

### 4.1 과거 실수들
1. **localhost vs cloud 구분 안 함** - OpenCode 서버 실행问题了고 물어봄
2. **KEY provider 확인 안 함** - GEMINI/API 키 있는데 다른 방법 물어봄
3. **여러 선택지 제공** - "어떤 것으로 할까요?" 묻고 기다림
4. **검색 안 하고 추측** - 실제로 사용 가능한 모델인지 확인 안 함

### 4.2 올바른 흐름
```
1. .env의 KEY 내용 먼저 확인
2. KEY 종류별 기본 모델 파악 (.env의 KEY가 어느 provider인지)
3. 무료 모델이면 → 해당 모델로 설정
4. 설정 후 코드 수정
5. 에러 발생 시 → 서버 콘솔 로그 확인
```

---

## 5. 질문 대답Template

### Good
- "지금 바로 수정할게요."
- "분석 결과 ○○입니다. 이 플랜으로 진행할까요?"
- "설정 확인 완료. 코드 수정 완료."

### Bad
- "어떤 모델을 사용하시겠어요?"
- "어떤 방향으로 진행할까요?"
- ".opencode serves dulu?"
- "서버가 실행 중인지 확인이 필요합니다."

---

## 6. 현재 프로젝트 설정

| 항목 | 현재 값 | 변경 필요 |
|------|---------|-----------|
| Flask 포트 | 5000 | - |
| LLM Provider | opencode | - |
| base_url | https://opencode.ai/zen/v1 | 수정 필요 |
| model | big-pickle | 수정 필요 |
| .env KEY | OPENCODE_API_KEY | - |

---

## 7. 변경 필요 파일

| 파일 | 변경 내용 |
|------|----------|
| src/nlp_pipeline.py | base_url, model 수정 |

---

## 8. 핵심 체크리스트

항상 확인 Before 작업:
- [ ] .env의 KEY 종류 확인
- [ ] 어떤 provider의 KEY인지 파악
- [ ] 무료 모델인지 확인
- [ ] base_url 올바른지 확인 (localhost vs cloud)
- [ ] model 이름 확인