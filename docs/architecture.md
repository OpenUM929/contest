# 리더십 성향 추론 엔진 — 최종 통합 설계안 v2.0

> **v1.0 → v2.0 주요 변경 사항**
> - Context Layer 위치 재설계 (전단 + 후단 이중 구조)
> - M/N 동시 추출 시 충돌 감지 레이어 추가
> - Hybrid Trait 생성 기준 명시화
> - Confidence 계산 세분화 (일관성 지표 추가)
> - NLP 추출 방식 전제 조건 명시

---

## 1. 전체 구조 (End-to-End Flow v2)

```
[1] Raw Text
     ↓
[2] NLP 추출 레이어
     - Micro Label 추출 (M / N Code + Confidence)
     - M/N 동시 추출 시 충돌 플래그 세팅
     ↓
[3] Context Detection
     - context_tag 판별 (crisis / normal / innovation 등)
     - Required / Optional 가중치 사전 조정
     ↓
[4] Pattern Engine ★핵심
     - Required 체크
     - Hard Forbidden 체크 → 즉시 탈락
     - Soft Forbidden 감점
     - Optional 반영
     ↓
[5] Strength 계산
     ↓
[6] Confidence 계산 (v2: 일관성 지표 추가)
     ↓
[7] Resolution Layer
     - M/N 충돌 처리
     - Trait 간 충돌 / 보완 / 모순 처리
     - Hybrid 생성 (기준 명시)
     ↓
[8] Context 후단 보정
     - Trait 명칭 및 해석 재조정
     ↓
[9] 최종 성향 출력
```

**핵심 변경**: Context Layer를 전단(가중치 조정)과 후단(해석 보정) 두 곳에 배치

---

## 2. 데이터 구조 설계

### 2.1 Micro Label 구조

| 필드 | 타입 | 필수 | 설명 | 예시 |
|------|------|------|------|------|
| `label_id` | String | Yes | 고유 식별자 | `"M33-01"` |
| `type` | String | Yes | M(positive) / N(negative) | `"M"` |
| `parent_label` | String | Yes | 상위 레이블 코드 | `"L33"` |
| `weight` | Float | Yes | 기본 가중치 (0~1) | `0.8` |
| `conflict_axis` | String | Yes | 충돌 감지용 축 정의 | `"L33"` |
| `description` | String | Yes | Micro Label 설명 | `"상위자 반대"` |
| `semantic_keywords` | Array[String] | Yes | 의미 기반 검색용 키워드 | `["상위자", "반대", "이의제기"]` |
| `dimension` | Array[String] | Yes | 행동 차원 | `["behavioral", "emotional"]` |
| `difficulty_level` | String | Yes | 관찰 난이도 | `"hard"` |
| `frequency_weight` | Float | Yes | 빈도 가중치 | `1.0` |

**특징**:
- 중복 허용 (중요)
- 여러 상위 레이블에 기여 가능
- NLP confidence 반드시 포함
- `conflict_axis`: 동일 축에서 M/N 동시 등장 시 충돌 플래그

### 2.2 Trait 정의 구조

| 필드 | 타입 | 설명 |
|------|------|------|
| `trait_id` | String | 고유 식별자 |
| `trait_name` | String | Trait 이름 |
| `context_weight` | Object | 상황별 Required 가중치 조정 |
| `required` | Array[Object] | 필수 Micro Label 목록 |
| `optional` | Array[Object] | 선택 Micro Label 목록 |
| `hard_forbidden` | Array[String] | 즉시 탈락 Micro Label |
| `soft_forbidden` | Array[Object] | 감점 Micro Label |
| `hybrid_eligible` | Array[Object] | Hybrid 생성 가능 조합 |
| `description` | String | Trait 설명 |
| `strengths` | Array[String] | 강점 목록 |
| `risks` | Array[String] | 리스크 목록 |

**context_weight 예시**:
```json
{
  "crisis": { "required_multiplier": 1.2 },
  "normal": { "required_multiplier": 1.0 },
  "innovation": { "required_multiplier": 0.9 }
}
```

**required/optional 객체 구조**:
```json
{
  "micro_code": "M33-01",
  "min_confidence": 0.7,
  "weight": 0.9
}
```

---

## 3. NLP 추출 레이어 (v2 신설)

### 3.1 전제 조건 명시

추출 방식에 따라 confidence의 의미가 달라지므로 사전에 방식을 확정하고 설계에 고정해야 한다.

| 방식 | 설명 | confidence 의미 | 장점 | 단점 |
|------|------|-----------------|------|------|
| **A. Rule-based** | 키워드/패턴 매칭 | 매칭 강도 (0~1 스케일링) | 설명 가능성 높음 | 표현 다양성 대응 한계 |
| **B. 분류 모델** | Micro Label별 이진 분류기 | softmax 확률값 | 다양한 표현 대응 | 레이블별 학습 데이터 필요 |
| **C. LLM 프롬프팅** | 프롬프트로 Micro Label 추출 지시 | LLM 자체 확신도 or 반복 추출 일치율 | 빠른 프로토타이핑 | 재현성 불안정 |

**권장**: 설계 단계에서 방식 C로 시작 → 방식 B로 고도화

### 3.2 M/N 동시 추출 충돌 감지

| 케이스 | 조건 | 처리 |
|--------|------|------|
| **Hard Conflict** | 같은 문장/발화에서 동시 추출 | Resolution Layer에서 우선 처리, 출력에 "행동 일관성 낮음" 경고 |
| **Soft Conflict** | 다른 시점/문장에서 추출 | Confidence 감산 (-0.1), 출력에 "상황별 편차 있음" 메모 |
| **빈도 불균형** | M 다수 / N 소수 | 플래그 없음, 정상 처리, Soft Forbidden 감점만 적용 |

---

## 4. Context Layer (v2: 전단 + 후단 이중 구조)

### 4.1 전단 Context (Pattern Engine 진입 전)

`context_tag`에 따라 Required / Optional 가중치를 사전 조정

| context_tag | 조정 내용 |
|-------------|-----------|
| **crisis** | Required 판정 임계값 완화 (1개 미충족 허용 → Weak로 처리), M19-01/M20-01 Required로 격상 |
| **normal** | 기본값 유지 |
| **innovation** | M23-01, M23-02 Required 가중치 ×1.2, M24-01 Optional로 격하 |

**적용 원칙**:
- `context_weight`는 Trait 정의서에 사전 기재
- 미기재 Trait는 normal 기본값 적용

### 4.2 후단 Context (출력 직전 해석 보정)

| 조합 | 보정 결과 |
|------|-----------|
| 통제형 리더 + crisis | "문제 해결형 리더"로 명칭 보정 |
| 공감형 리더 + crisis | "위기 안정화 리더"로 명칭 보정 |
| 혁신형 리더 + normal | 원래 명칭 유지 |

출력 시 `context_tag`와 보정 여부를 함께 표시

---

## 5. Pattern Engine 로직

### 5.1 기본 판정 흐름

```
1. Required 모두 존재?
   → NO → context가 crisis이면 Weak로 허용, 아니면 탈락

2. Hard Forbidden 존재?
   → YES → Trait = 0 (즉시 탈락)

3. M/N 충돌 플래그 확인
   → Hard Conflict → Confidence 강제 Low
   → Soft Conflict → Confidence 감산

4. Optional 개수 계산

5. Soft Forbidden 감점 적용

6. Strength 계산
```

---

## 6. Strength 계산 로직

### 6.1 계산 공식

```
Strength =
  (Required 기여도 합 × context_weight)
+ (Optional 기여도 합)
- (Soft Forbidden 패널티)
```

### 6.2 상세 구성

| 구성 요소 | 공식 |
|-----------|------|
| Required | `weight × NLP confidence × context_weight` |
| Optional | `weight × confidence` |
| Soft Forbidden | `penalty × confidence` |

결과: **0 ~ 1로 정규화**

### 6.3 Level 기준

| Strength | Level |
|----------|-------|
| 0.8 이상 | Strong |
| 0.5 ~ 0.8 | Moderate |
| 0.5 미만 | Weak |

---

## 7. Confidence 계산 로직 (v2: 일관성 지표 추가)

### 7.1 계산 요소

| 요소 | 비중 | 설명 |
|------|------|------|
| **A. 데이터 양 기반 점수** | 0.3 | 관찰 개수 기반 |
| **B. NLP 추출 신뢰도 평균** | 0.5 | 각 Label의 confidence 평균 |
| **C. 일관성 지표** | 0.2 | 동일 Micro Label이 여러 맥락에서 반복 등장한 비율 |

**일관성 지표 공식**:
```
일관성 = 고유 맥락 수 / 전체 등장 횟수
```

예) M33-01이 5회 등장 중 4회가 서로 다른 맥락 → 일관성 0.8

### 7.2 계산 공식

```
Confidence =
  (데이터 양 기반 점수 × 0.3)
+ (평균 NLP confidence × 0.5)
+ (일관성 지표 × 0.2)
```

### 7.3 결과 등급

| Confidence | Level |
|------------|-------|
| 0.75 이상 | High |
| 0.45 ~ 0.75 | Medium |
| 0.45 미만 | Low |

**M/N Hard Conflict 존재 시 → 등급 강제 Low**

---

## 8. Forbidden 체계

### 8.1 Hard Forbidden
- 성향 자체를 무효화
- 예: 윤리 위반, 인격적 공격
- 역할: **"성향 정체성 붕괴"**

### 8.2 Soft Forbidden
- 성향 약화
- 리스크로 출력
- 역할: **"성향 품질 저하"**

---

## 9. Resolution Layer (v2: 충돌 유형 세분화)

### 9.1 M/N 충돌 처리 (v2 신설)

| 유형 | 조건 | 처리 |
|------|------|------|
| **Hard Conflict** | 동일 문장/발화 | 해당 Trait Confidence = Low 강제, 출력에 "행동 일관성 낮음" 경고 |
| **Soft Conflict** | 다른 시점/문장 | Confidence 감산 (-0.1), 출력에 "상황별 편차 있음" 메모 |

### 9.2 Trait 간 처리

| 관계 | 처리 |
|------|------|
| **경쟁 관계** | Strength 높은 Trait 선택 |
| **보완 관계** | Hybrid Trait 생성 (조건 충족 시) |
| **모순 관계** | 판단 유보 + Low Confidence 출력 |

---

## 10. Hybrid Trait 생성 기준 (v2 명시화)

### 10.1 생성 원칙
- 사전 **화이트리스트** 방식으로만 허용
- 임의 조합 금지 (구현 시 일관성 확보)
- 등록 기준: 동일 대분류 or 상호 보완 관계 이론 기반

### 10.2 허용 기준 예시

**보완 허용 (같은 방향성)**:
| 조합 | Hybrid 이름 |
|------|-------------|
| T01 보호형 도덕 리더 + T14 변화 주도 혁신가 | 전략적 보호자 |
| T01 보호형 도덕 리더 + T05 심리적 안전 창출자 | 심리적 수호자 |
| T06 성장 촉진 코치형 + T15 실험적 탐험가 | 혁신 성장 촉진자 |

**모순 처리 (상충 방향성)**:
| 조합 | 처리 |
|------|------|
| T23 통제형 관리자 + T05 심리적 안전 창출자 | Hybrid 불가, 모순 처리 |
| T08 실행 중심 드라이버 + T21 합의 지향 조정자 | Hybrid 불가, Strength 높은 것만 Primary 출력 |

### 10.3 확장 방식

신규 Hybrid 추가 시:
1. 이론적 근거 기재 필수
2. 두 Trait의 대분류 관계 명시
3. `hybrid_eligible` 테이블에 양방향 등록

---

## 11. 최종 출력 구조 (v2)

```json
{
  "primary_trait": {
    "trait_id": "T01",
    "trait_name": "보호형 도덕 리더",
    "strength": "Strong",
    "confidence": "High",
    "context": "normal",
    "context_adjustment": "보정 없음"
  },
  "secondary_traits": [
    {
      "trait_id": "T02",
      "trait_name": "데이터 기반 혁신가",
      "strength": "Moderate"
    }
  ],
  "hybrid_trait": {
    "name": "전략적 보호자",
    "components": ["T01", "T14"]
  },
  "conflict_flags": {
    "L33": {
      "type": "soft_conflict",
      "message": "상황별 편차 있음"
    }
  },
  "risks": [
    "조직 갈등 증가 가능성"
  ],
  "evidence": [
    {
      "micro_code": "M33-01",
      "confidence": 0.92,
      "count": 3,
      "context_consistency": 0.9
    },
    {
      "micro_code": "M33-03",
      "confidence": 0.88,
      "count": 2,
      "context_consistency": 0.8
    }
  ],
  "theory_mapping": {
    "primary": ["Ethical Leadership", "Servant Leadership"],
    "validation_note": "본 모델은 Transformational, Servant, Ethical Leadership 이론을 기반으로, 행동 단위(Micro Label)와 패턴 매칭을 통해 동적 성향을 추론하도록 재구성한 응용 모델이다."
  }
}
```

---

## 12. 이론 매핑 (Validation Layer)

### 목적
- 외부 검증 대응 / 모델 신뢰성 확보

### 기준 이론
- Transformational Leadership
- Servant Leadership
- Ethical Leadership
- Adaptive Leadership
- Ambidextrous Leadership
- Data-Driven Decision Making

### 핵심 차별성 한 문장
> "본 모델은 Transformational, Servant, Ethical Leadership 이론을 기반으로, 행동 단위(Micro Label)와 패턴 매칭을 통해 동적 성향을 추론하도록 재구성한 응용 모델이다."

### 기존 이론 대비 차별점

| 요소 | 기존 이론 | 본 모델 |
|------|-----------|---------|
| **구조** | 유형(고정) | 패턴(동적) |
| **입력** | 설문 | 행동 텍스트 |
| **결과** | 고정 분류 | 상황 기반 추론 |
| **해석** | 단일 유형 | 복합 / Hybrid 허용 |

---

## 13. 파일 구조

```
leadership-eval/
│
├── data/                           # 데이터 레이어
│   ├── micro_labels/
│   │   ├── positive_micro_labels.json    # 긍정 Micro Label 전체
│   │   └── negative_micro_labels.json    # 부정 Micro Label 전체
│   │
│   ├── labels/
│   │   ├── positive_labels.json          # 긍정 Label 31개
│   │   └── negative_labels.json          # 부정 Label 37개
│   │
│   ├── traits/
│   │   ├── trait_definitions.json        # 25개 Trait 정의
│   │   └── trait_theory_mapping.json     # Trait ↔ 이론 매핑
│   │
│   ├── mappings/
│   │   ├── label_to_micro_mapping.json   # Label → Micro Label
│   │   └── cross_weights.json            # 교차 가중치
│   │
│   ├── engine/
│   │   ├── pattern_rules.json            # Pattern Engine 규칙
│   │   ├── resolution_rules.json         # 충돌 해결 규칙
│   │   └── context_rules.json            # 상황별 보정 규칙
│   │
│   └── schema/
│       └── leadership_eval_schema.json   # JSON Schema
│
├── docs/
│   └── architecture.md             # 이 파일
│
└── src/                            # 소스 코드 (향후)
    ├── extractor.py                # Micro Label 추출기
    ├── pattern_engine.py           # 패턴 엔진
    ├── strength_calculator.py      # 점수 계산기
    ├── resolution_layer.py         # 충돌 해결
    └── context_layer.py            # 상황 보정
```

---

## 14. 구현 단계 (Step-by-Step)

| 단계 | 작업 | 내용 |
|------|------|------|
| **Step 1** | Micro Label 정의서 데이터화 | 긍정/부정 Micro Label 전체 JSON 구조화 |
| **Step 2** | Label 정의서 데이터화 | 31개 긍정 + 37개 부정 Label JSON |
| **Step 3** | 매핑 테이블 생성 | Label ↔ Micro Label + 교차 가중치 |
| **Step 4** | Trait 정의서 생성 | 25개 Trait (Required/Optional/Forbidden/Hybrid) |
| **Step 5** | Trait ↔ 이론 매핑 | 25개 Trait ↔ 6개 이론 매핑 JSON |
| **Step 6** | Pattern Engine 규칙 | Strength/Confidence 계산 로직 정의 |
| **Step 7** | Resolution 규칙 | M/N 충돌 + Trait 간 충돌 해결 |
| **Step 8** | Context 규칙 | 상황별 가중치 조정 + 해석 보정 |
| **Step 9** | JSON Schema | 전체 데이터 구조 검증용 스키마 |

---

## 15. v2 변경 요약

| 변경 항목 | 내용 |
|-----------|------|
| 1 | **Context Layer 이중화** (전단 가중치 조정 + 후단 해석 보정) |
| 2 | **M/N 동시 추출 충돌 감지 레이어** 신설 |
| 3 | **Hybrid Trait 화이트리스트** 기준 명시화 |
| 4 | **Confidence 계산에 일관성 지표(0.2)** 추가 |
| 5 | **NLP 추출 방식 전제 조건** 명시 (A/B/C 방식) |
| 6 | **출력 구조에 Conflict Flags 및 맥락 일관성** 추가 |

---

*문서 버전: v2.0 | 작성일: 2026-04-07*