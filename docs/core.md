# Leadership Analysis System - Core Pipeline Specification

> **표준 파이프라인 구조 정의서**  
> 버전: 2.1 (2026-05-18)  
> 작성자: AI Assistant

**참고:** 파일 구조 및 라벨 계층도는 [FILE_STRUCTURE.md](../FILE_STRUCTURE.md)를 참조하세요.

---

## 1. 개요

리더십 분석 시스템의 핵심 파이프라인은 **Vector DB 하이브리드 추출 엔진**을 표준으로 합니다.  
LLM(Gemini/OpenCode)은 Vector DB의 신뢰도 임계값에 따라 조걶으로 호출됩니다.

**현재 데이터 규모:**
- 178개 마이크로 라벨 (Positive 98 + Negative 80)
- 12,460개 학습 샘플 (라벨당 70개)
- KoE5 임베딩 + FAISS 인덱스 (768-dim)

---

## 2. 표준 파이프라인 구조

```
[사용자 입력 텍스트]
         ↓
[Step 1: Vector DB 검색] ← KoE5 + FAISS (178개 라벨 대상)
         ↓
[Step 2: 임계값 판단] ← should_call_llm() (0.70 / 0.60)
         ↓
    ┌────┴────┐
    ↓         ↓
[Vector Only]  [Step 3: LLM 추론]
    ↓         ↓
    └────┬────┘
         ↓
[Step 4: 후처리] ← Calibration, 필터링, Conflict 처리
         ↓
[Step 5: Trait 추론] ← LeadershipEngine
         ↓
[Step 6: 결과 구성] ← JSON 응답
```

---

## 3. 핵심 컴포넌트

### 3.1 VectorSearcher (`src/vector_search.py`)

- `search(text, k=15, expand=True)` — 벡터 검색 (label_id, confidence, distance 반환)
- `should_call_llm(results, threshold_high=0.70, threshold_low=0.60)` — LLM 호출 여부 판단
- `check_adversative_particles(text)` — 역접 형태소 확인 ("하지만", "않았" 등)
- **쿼리 확장:** 위기/혁신/부정 키워드 가중치 부여

### 3.2 NLP Pipeline (`src/nlp_pipeline.py`)

- 하이브리드 파이프라인 엔트리 포인트
- Vector-only 모드와 LLM 호출 모드 자동 분기
- Calibration (×0.88), 필터링 (threshold=0.5), Conflict 감지

### 3.3 LeadershipEngine (`src/leadership_engine.py`)

- Micro Label → Trait 점수 변환
- Primary/Secondary Trait 결정
- Negative Trait severity 계산

---

## 4. 임계값 설정

| 구분 | 임계값 | 설명 |
|------|---------|------|
| High Confidence | ≥0.70 | Vector DB만으로 충분히 확신 → LLM 스킵 |
| Mid Confidence | 0.60-0.69 | LLM 추론 필요 (Vector DB 참고) |
| Low Confidence | <0.60 | 매칭 없음 |
| Calibration | ×0.88 | LLM confidence 과대 추정 보정 |
| Low Filter | 0.50 | 추출 후 0.5 미만 라벨 제거 |

**역접 형태소는 무조건 LLM 호출:**  
`["하지만", "그러나", "~않다", "않았", "않고", "~못하다", "못했", "못하"]`

---

## 5. API 응답 포맷

```json
{
  "success": true,
  "input_text": "...",
  "extracted_labels": {"sentences": [...]},
  "trait_result": {
    "primary": "T04",
    "primary_name": "Crisis Manager",
    "trait_percentages": [...],
    "negative_traits": [...]
  },
  "vector_results": [...],
  "vector_meta": {
    "vector_only": false,
    "used_llm": true
  }
}
```

---

## 6. 테스트 시나리오

| 시나리오 | 입력 특징 | 기대 결과 |
|----------|-----------|-----------|
| T04-B (위기) | "문제가 발생... 빠르게 결론" | M19-01, M20-01 검출 → T04 |
| T105-A (역접) | "하지만 실제로는..." | LLM 강제 호출 → N02-02, N02-03 |
| 고신뢰도 | 명확한 키워드 매치 | Vector DB만으로 스킵 |
| 중신뢰도 | 애매한 맥락 | LLM 호출 후 판단 |

---

## 7. 배포 체크리스트

- [ ] `build_vector_db.py` 실행 (178개 라벨 기준)
- [ ] FAISS 인덱스 정상 로드 확인
- [ ] Flask 서버 디버그 모드 해제
- [ ] API 키 및 환경 변수 설정
- [ ] CORS 설정 확인

---

## 8. 자주 발생하는 오류

| 오류 | 원인 | 해결 |
|------|------|------|
| `FaissError` | 인덱스 손상/불일치 | `python build_vector_db.py` 재실행 |
| `ValueError: allowed_labels` | 라벨 스키마 로드 실패 | `dataset/ori/*_enhanced.json` 경로 확인 |
| `JSONDecodeError` | LLM 코드블록 포함 출력 | 프롬프트에 "순수 JSON만" 규칙 강화 |
| `Threshold too high` | Vector DB 신뢰도 낮음 | 임계값 0.70→0.75 조정 검토 |

---

> **작성 원칙:**
> 1. 모든 분석은 Vector DB를 거친다
> 2. 임계값 기반 조걶 LLM 호출
> 3. 디버그 정보는 모든 단계에서 수집
> 4. 프론트엔드는 Vector DB 결과를 반드시 표시
