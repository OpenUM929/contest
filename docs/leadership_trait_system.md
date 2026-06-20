# 리더십 Trait 시스템 문서화

**문서 버전**: v1.0  
**작성일**: 2026-04-23  
**시스템 버전**: Leadership Engine v3.0

---

## 1. 개요

### 1.1 목적
본 문서는 리더십 성향 추론 시스템의 Trait 구조, Label 체계, 그리고 추론 엔진의 동작 원리를 문서화하여 시스템 이해도와 유지보수성을 높이는 것을 목적으로 한다.

### 1.2 시스템 구조
```
┌─────────────────────────────────────────────────────────────┐
│                     리더십 분석 시스템                         │
├─────────────────────────────────────────────────────────────┤
│  1. 텍스트 입력                                              │
│  2. LLM이 Micro Labels 추출 (Mxx: 긍정, Nxx: 부정)           │
│  3. LeadershipEngine가 Trait 추론                           │
│  4. Primary/Secondary Trait 결정                            │
│  5. Strengths/Risks 조회 및 결과 반환                        │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 주요 파일
| 파일 | 설명 |
|------|------|
| `src/leadership_engine.py` | Trait 추론 엔진 |
| `src/nlp_pipeline.py` | LLM 파이프라인 |
| `data/traits/trait_definitions.json` | Trait 정의 |
| `data/micro_labels/positive_micro_labels.json` | 긍정 Label (67개) |
| `data/micro_labels/negative_micro_labels.json` | 부정 Label (58개) |

---

## 2. Trait 계층 구조

### 2.1 전체 Trait 목록 (18개)

```
리더십 Trait 시스템
│
├── Positive Traits (14개) - T01~T14
│   │
│   ├── T01: Strategic Decisive Leader    [결단형]
│   ├── T02: Collaborative Leader         [협업형]
│   ├── T03: Innovative Leader            [혁신형]
│   ├── T04: Crisis Manager              [위기 대응형]
│   ├── T05: Analytical Leader           [분석형]
│   ├── T06: Execution Driver            [실행형]
│   ├── T07: Coaching Leader            [코칭형]
│   ├── T08: Emotional Intelligence Leader [감정 지능형]
│   ├── T09: Visionary Leader            [비전 제시형]
│   ├── T10: (reserved)
│   ├── T11: (reserved)
│   ├── T12: Balanced Leader            [균형형]
│   ├── T13: Ethical Courageous Leader  [윤리적 용기형]
│   └── T14: Learning Agile Leader      [학습 민첩형]
│
└── Negative Traits (6개) - T101~T106
    │
    ├── T101: Risk: Avoidant             [회피형]
    ├── T102: Risk: Authoritarian        [권위주의]
    ├── T103: Risk: Integrity Violation [정직성 위반]
    ├── T104: Risk: Narcissistic Leadership [자기애적]
    ├── T105: Risk: Manipulative Leadership [조작적]
    └── T106: Risk: Volatile Leadership [기복형]
```

### 2.2 Trait 분류 로직 (leadership_engine.py:22-26)

```python
# Negative Trait ID 명시적 지정
self.negative_trait_ids = {'T101', 'T102', 'T103', 'T104', 'T105', 'T106'}

# Positive Traits: Negative Trait ID가 아닌 것
self.positive_traits = [t for t in self.trait_definitions 
                       if t['trait_id'] not in self.negative_trait_ids]

# Negative Traits: 명시적 ID 매칭
self.negative_traits = [t for t in self.trait_definitions 
                        if t['trait_id'] in self.negative_trait_ids]
```

---

## 3. Positive Trait 상세 정의

| Trait ID | Name | Required Labels | Optional Labels | Hard Forbidden | Strengths | Risks |
|----------|------|-----------------|-----------------|----------------|-----------|-------|
| T01 | Strategic Decisive Leader | M01-01, M06-01, M10-01 | M01-02, M06-02, M19-01 | N08-01, N08-02, N14-01 | 빠른 판단, 책임감, 방향성 명확 | 성급한 결정, 구성원 의견 배제 |
| T02 | Collaborative Leader | M11-01, M15-01, M15-03 | M11-02, M12-01, M12-02 | N11-01, N11-02, N15-03, N04-02 | 팀 결속, 갈등 완화 | 결정 지연 |
| T03 | Innovative Leader | M03-03, M05-02, M23-01 | M03-01, M03-02, M23-02 | N03-01, N03-02, N05-03 | 혁신 창출, 미래 지향 | 현실성 부족 |
| T04 | Crisis Manager | M19-01, M10-01, M20-01 | M18-01, M17-01 | N18-01, N18-02 | 긴급 대응, 결단력 | 평시 과도한 통제 |
| T05 | Analytical Leader | M34-01 | M08-02, M18-02 | N01-02, N28-01 | 정확성, 논리성 | 결정 지연 |
| T06 | Execution Driver | M10-01, M10-02 | M19-01, M27-01 | N10-02, N27-01 | 빠른 실행, 성과 창출 | 전략 부족 |
| T07 | Coaching Leader | M02-02, M07-02 | M02-01, M02-03 | N07-02, N14-02 | 인재 육성, 조직 성장 | 성과 지연 |
| T08 | Emotional Intelligence Leader | M12-01, M14-01 | M11-01, M12-02, M12-03 | N12-01, N12-02, N12-03 | 관계 형성, 심리 안정 | 결단력 부족 |
| T09 | Visionary Leader | M01-01, M01-04 | M01-02, M02-01 | N01-03 | 방향성 제시, 동기부여 | 현실성 부족 |
| T12 | Balanced Leader | (none) | M24-01, M28-01, M31-01 | N28-01, N30-01, N31-01 | 안정성, 적응력 | 특색 부족 |
| T13 | Ethical Courageous Leader | M33-01, M33-04, M33-05 | M33-02, M33-03 | N33-01, N33-02 | 윤리적 용기, 정의 실천 | 정치적 현실主義 |
| T14 | Learning Agile Leader | M21-01, M22-01, M32-01 | M21-02, M22-02, M32-02 | N22-01, N22-02 | 지속 학습, 빠른 적응 | 과도한 실험

### 3.1 Positive Trait 수식어

| 수식어 | 설명 |
|--------|------|
| `required` | Trait 발동에 필수적인 Label (모두 충족 필요) |
| `optional` | Trait 발동에 가산되는 Label |
| `hard_forbidden` | 해당 Label 발견 시 Trait 즉시 무효화 |
| `soft_forbidden` | 해당 Label 발견 시 penalty 적용 |

---

## 4. Negative Trait 상세 정의

| Trait ID | Name | Required Labels | Optional Labels | Strengths | Risks |
|----------|------|-----------------|-----------------|-----------|-------|
| T101 | Risk: Avoidant | N08-01, N08-02 | N10-01, N14-01 | (없음) | 책임 회피, 의사결정 지연 |
| T102 | Risk: Authoritarian | N15-03, N19-01 | N04-02, N15-01, N15-02 | (없음) | 팀 반발, 창의성 저해 |
| T103 | Risk: Integrity Violation | N30-01, N28-01 | N01-03 | (없음) | 신뢰도 저하, 조직 문화 훼손 |
| T104 | Risk: Narcissistic Leadership | N04-01, N14-01 | N14-02, N15-05 | (없음) | 팀士气 저하, 혁신 저해 |
| T105 | Risk: Manipulative Leadership | N02-01, N02-02 | N02-03, N09-01 | (없음) | 신뢰도 붕괴, 장기적 성과 저하 |
| T106 | Risk: Volatile Leadership | N18-01, N18-02 | N19-01, N22-01 | (없음) | 불안定的 환경, 직원 이직

### 4.1 Negative Trait 발동 조건

2026-04-23 수정: Partial Match 지원 (50% threshold)

```python
def _calculate_negative_trait(self, trait_def, label_ids, label_confidences):
    required = trait_def.get('required', [])
    present_required = [r for r in required if r in label_ids]
    
    if required:
        req_ratio = len(present_required) / len(required)
        if req_ratio < 0.5:
            return 0  # 50% 이상 충족해야 발동
```

---

## 5. Micro Label 분류 체계

### 5.1 Positive Micro Labels (Mxx) - 총 67개

```
Micro Labels (Positive)
│
├── M01: 비전 제시 (4개) - M01-01~M01-04
├── M02: 동기 부여 (4개) - M02-01~M02-04
├── M03: 창의성 (3개) - M03-01~M03-03
├── M04: 카리스마 (2개) - M04-01~M04-02
├── M05: 변화 리드 (3개) - M05-01~M05-03
├── M06: 목표 설정 (2개) - M06-01~M06-02
├── M07: 피드백 (2개) - M07-01~M07-02
├── M08: 원칙 준수 (2개) - M08-01~M08-02
├── M09: 공정한 인정 (1개) - M09-01
├── M10: 실행 (2개) - M10-01~M10-02
├── M11: 경청 (2개) - M11-01~M11-02
├── M12: 감정 이해 (3개) - M12-01~M12-03
├── M14: 이타적 행동 (2개) - M14-01~M14-02
├── M15: 심리적 안전 (6개) - M15-01~M15-06
├── M17: 상황 적응 (1개) - M17-01
├── M18: 안정감 (2개) - M18-01~M18-02
├── M19: 신속 판단 (1개) - M19-01
├── M20: 문제 해결 (1개) - M20-01
├── M21: 지속 학습 (2개) - M21-01~M21-02
├── M22: 실패 수용 (2개) - M22-01~M22-02
├── M23: 기회 탐색 (2개) - M23-01~M23-02
├── M24: 운영 안정 (1개) - M24-01
├── M26: 도전 장려 (1개) - M26-01
├── M27: 자원 배분 (1개) - M27-01
├── M28: 정보 공유 (2개) - M28-01~M28-02
├── M30: 언행 일치 (1개) - M30-01
├── M31: 다양성 존중 (1개) - M31-01
├── M32: 자기 성찰 (2개) - M32-01~M32-02
├── M33: 도덕적 용기 (5개) - M33-01~M33-05
├── M34: 데이터 기반 (1개) - M34-01
├── M35: 디지털 활용 (1개) - M35-01
└── M37: AI 활용 (2개) - M37-01~M37-02
```

### 5.2 Negative Micro Labels (Nxx) - 총 58개

```
Micro Labels (Negative)
│
├── N01: 비전 왜곡 (3개) - N01-01~N01-03
├── N02: 동기 조작 (3개) - N02-01~N02-03
├── N03: 지적 억압 (3개) - N03-01~N03-03
├── N04: 카리스마 악용 (2개) - N04-01~N04-02
├── N05: 변화 강요 (3개) - N05-01~N05-03
├── N06: 목표 모호화 (2개) - N06-01~N06-02
├── N07: 성과 기반 비난 (2개) - N07-01~N07-02
├── N08: 책임 전가 (3개) - N08-01~N08-03 ⚠️ Critical
├── N09: 불공정 인정 (2개) - N09-01~N09-02
├── N10: 실행 방해 (2개) - N10-01~N10-02
├── N11: 경청 거부 (2개) - N11-01~N11-02
├── N12: 공감 결여 (3개) - N12-01~N12-03
├── N14: 이기적 행동 (3개) - N14-01~N14-03
├── N15: 심리적 안전 파괴 (6개) - N15-01~N15-06 ⚠️ Critical
├── N17: 상황적 강경 (1개) - N17-01
├── N18: 불안 조장 (2개) - N18-01~N18-02
├── N19: 독단 결정 (1개) - N19-01
├── N21: 디지털 저항 (1개) - N21-01
├── N22: 실패 부정 (2개) - N22-01~N22-02
├── N23: 혁신 방해 (1개) - N23-01
├── N24: 과도 통제 (1개) - N24-01
├── N26: 실험 처벌 (1개) - N26-01
├── N27: 자원 독점 (1개) - N27-01
├── N28: 투명성 위반 (1개) - N28-01 ⚠️ Critical
├── N30: 언행 불일치 (1개) - N30-01
├── N31: 포용성 위반 (1개) - N31-01
├── N33: 도덕적 용기 결여 (2개) - N33-01~N33-02
├── N34: 데이터 조작 (1개) - N34-01 ⚠️ Critical
├── N35: 디지털 도구 남용 (1개) - N35-01
└── N37: AI 악용 (1개) - N37-01
```

### 5.3 Critical Negative Labels (4개)

단일 발생으로도 Trait 붕괴 또는 조직 수준의 심각한 리스크를 유발하는 Label:

| Label ID | Name | Risk Level | Impact |
|----------|------|------------|--------|
| N08-01 | 직접 책임 전가 | Critical | 조직 신뢰 붕괴 |
| N15-03 | 공개적 비난 | Critical | 심리적 안전 파괴 |
| N28-01 | 정보 은폐 | Critical | 투명성 위반 |
| N34-01 | 데이터 조작 | Critical | 시스템 신뢰 붕괴 |

---

## 6. Label-Trait Coverage 분석

### 6.1 Coverage 현황 (2026-04-23 기준)

| 분류 | 전체 Label | Trait에 매핑됨 | 미매핑 |
|------|-----------|---------------|--------|
| Positive (Mxx) | 67개 | 67개 (100%) | **0개 (0%)** |
| Negative (Nxx) | 58개 | 58개 (100%) | **0개 (0%)** |
| **합계** | **125개** | **125개 (100%)** | **0개 (0%)** |

> 2026-04-23: T13, T14 및 새 Negative Traits (T104~T106) 추가로 100% 매핑 달성

### 6.2 ~ 6.3 (미매핑 Label 목록)

> **2026-04-23 업데이트**: 모든 Label이 Trait에 매핑됨 (미매핑 0개)

### 6.2 Label-Trait 매핑 상세

| 분류 | 매핑된 Traits |
|------|-------------|
| Positive Labels (67개) | T01~T09, T12, T13, T14 |
| Negative Labels (58개) | T101~T106 |

---

## 7. 추론 엔진 흐름도

### 6.3 미매핑 Negative Labels (29개)

| Label ID | Macro | Name | 미매핑 이유 |
|----------|-------|------|------------|
| N01-01 | N01 | 비현실적 목표 제시 | Trait required/optional 미지정 |
| N02-01 | N02 | 공포 기반 동기 유도 | Trait required/optional 미지정 |
| N02-02 | N02 | 보상 과장 약속 | Trait required/optional 미지정 |
| N02-03 | N02 | 감정적 압박 | Trait required/optional 미지정 |
| N03-03 | N03 | 질문 억제 | Trait required/optional 미지정 |
| N04-01 | N04 | 개인 숭배 유도 | Trait required/optional 미지정 |
| N05-01 | N05 | 의견 없이 변화 강행 | Trait required/optional 미지정 |
| N05-02 | N05 | 준비 없는 변화 추진 | Trait required/optional 미지정 |
| N06-02 | N06 | 우선순위 불명확 | Trait required/optional 미지정 |
| N07-01 | N07 | 성과만으로 평가 | Trait required/optional 미지정 |
| N08-03 | N08 | 성과 가로채기 | Trait required/optional 미지정 |
| N09-01 | N09 | 편파적 평가 | Trait required/optional 미지정 |
| N09-02 | N09 | 차별적 보상 | Trait required/optional 미지정 |
| N14-03 | N14 | 팀 희생 강요 | Trait required/optional 미지정 |
| N15-04 | N15 | 실수 처벌 | Trait required/optional 미지정 |
| N15-05 | N15 | 불신 조장 | Trait required/optional 미지정 |
| N15-06 | N15 | 보복 암시 | Trait required/optional 미지정 |
| N17-01 | N17 | 상황 무시 강경 대응 | Trait required/optional 미지정 |
| N21-01 | N21 | 디지털 거부 | Trait required/optional 미지정 |
| N22-01 | N22 | 실패 은폐 | Trait required/optional 미지정 |
| N22-02 | N22 | 책임 회피 학습 차단 | Trait required/optional 미지정 |
| N23-01 | N23 | 혁신 아이디어 차단 | Trait required/optional 미지정 |
| N24-01 | N24 | 과도한 통제 | Trait required/optional 미지정 |
| N26-01 | N26 | 실험 실패 처벌 | Trait required/optional 미지정 |
| N33-01 | N33 | 부당행위 묵인 | Trait required/optional 미지정 |
| N33-02 | N33 | 문제 회피 | Trait required/optional 미지정 |
| N34-01 | N34 | 데이터 조작 | **Critical Label이나 미매핑** |
| N35-01 | N35 | 도구 남용 | Trait required/optional 미지정 |
| N37-01 | N37 | AI 부정 사용 | Trait required/optional 미지정 |

### 6.4 미매핑 Label로 인한 문제

1. **Trait 추론 부정확**: 미매핑 Label이 추출되어도 Strength 계산에 반영 안됨
2. **Partial Trait 발동 불가**: 일부 Label만 있어도 Trait 미발동
3. **LLM 확장 트리거 무시**: nlp_pipeline.py에 정의된 강제 확장 규칙이 Trait에 연결 안됨

---

## 7. 추론 엔진 흐름도

### 7.1 전체 흐름

```
┌─────────────────────────────────────────────────────────────────┐
│                       입력 텍스트                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: LLM Micro Label 추출                                   │
│  - build_llm_prompt(): 프롬프트 생성                            │
│  - call_llm_with_retry(): LLM 호출 + 검증                      │
│  - validate_structure(): 구조 검증                              │
│  - apply_calibration(): confidence 보정                         │
│  - filter_low_confidence(): threshold < 0.5 제거                │
│  - apply_sentence_weights(): 중요도 가중치                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 2: Trait 추론 (leadership_engine.py)                       │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 2.1 Positive Trait 계산 (_calculate_positive_trait)      │   │
│  │   - Required Labels 매칭 확인                            │   │
│  │   - Optional Labels 매칭 확인                            │   │
│  │   - Hard Forbidden 체크 (Trait 즉시 무효)                 │   │
│  │   - Soft Forbidden 패널티 적용                           │   │
│  │   - Context Weight 곱셈                                  │   │
│  │   - Strength 계산: log(1 + weighted_sum) / k_trait       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 2.2 Negative Trait 계산 (_calculate_negative_trait)      │   │
│  │   - Required Labels 매칭 확인                            │   │
│  │   - Partial Match 지원 (50% threshold)                   │   │
│  │   - Optional Labels 가산                                │   │
│  │   - Severity 계산: weighted_sum × k_trait               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 2.3 통합 Trait Percentages 계산                          │   │
│  │   - 긍정 + 부정 Strength 통합                            │   │
│  │   - total = sum(all_strengths)                          │   │
│  │   - percentage = (strength / total) × 100               │   │
│  │   - 3% 이상만 필터링                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 2.4 Primary Trait 결정                                   │   │
│  │   - trait_percentages[0] = Primary                       │   │
│  │   - type 필드로 positive/negative 구분                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 2.5 Risks 감지 (_detect_risks)                           │   │
│  │   - N-Label Count ≥ 2: Toxic Leader                      │   │
│  │   - Negative Trait Strength > 0.2: Dominance            │   │
│  │   - Critical Labels: N15-03, N28-01 등                  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 3: Strengths/Risks 조회                                   │
│  - get_trait_details(trait_id)                                  │
│  - trait_definitions.json에서 strengths, risks 가져오기         │
│  - Negative Trait: strengths = [], risks = ["팀 반발", ...]     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 4: 결과 반환                                              │
│                                                                 │
│  {                                                              │
│    "primary": "T102",                                            │
│    "primary_type": "negative",                                  │
│    "primary_name": "Risk: Authoritarian",                       │
│    "strengths": [],                                             │
│    "risks": ["팀 반발", "창의성 저해"],                           │
│    "trait_percentages": [                                       │
│      {"trait_id": "T102", "percentage": 53.6, "type": "negative"},│
│      {"trait_id": "T101", "percentage": 46.4, "type": "negative"} │
│    ],                                                            │
│    "negative_traits": [...],                                    │
│    "risks": [...]                                                │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Strength 계산 공식

```python
# Positive Trait
strength_raw = Σ (weight × confidence × context_weight × penalty_factor)
strength_log = log(1 + strength_raw)
strength = min(1.0, strength_log / k_trait)

# Negative Trait
severity_raw = Σ (weight × confidence)
severity = severity_raw × k_trait
```

### 7.3 Confidence 계산 공식

```python
confidence = (volume × 0.3) + (avg_nlp_conf × 0.5) + (consistency × 0.2)

where:
  volume = min(len(micro_labels) / 5, 1.0)
  avg_nlp_conf = average of label confidences
  consistency = average of (unique_contexts / count) per label
```

---

## 8. API 응답 구조

### 8.1 /api/analyze 응답

```json
{
  "success": true,
  "input_text": "분석할 텍스트",
  "mode": "auto|manual",
  "extracted_labels": {
    "sentences": [
      {
        "text": "문장 원문",
        "context": "crisis|normal|innovation",
        "labels": [
          {"label_id": "M10-01", "confidence": 0.9, "reason": "근거"}
        ]
      }
    ]
  },
  "trait_result": {
    "primary": "T06",
    "primary_type": "positive",
    "primary_name": "Execution Driver",
    "primary_description": "실행 중심의 성과 창출 리더",
    "primary_strength": 0.419,
    "strengths": ["빠른 실행", "성과 창출"],
    "risks": ["전략 부족"],
    "secondary": ["T01", "T04"],
    "secondary_details": [
      {"trait_id": "T01", "name": "Strategic Decisive Leader", "type": "positive"},
      {"trait_id": "T04", "name": "Crisis Manager", "type": "positive"}
    ],
    "confidence": 0.765,
    "confidence_level": "high",
    "trait_percentages": [
      {"trait_id": "T06", "name": "Execution Driver", "percentage": 41.3, "type": "positive"},
      {"trait_id": "T01", "name": "Strategic Decisive Leader", "percentage": 31.2, "type": "positive"},
      {"trait_id": "T04", "name": "Crisis Manager", "percentage": 27.4, "type": "positive"}
    ],
    "negative_traits": [
      {"trait_id": "T102", "name": "Risk: Authoritarian", "severity": 0.58}
    ],
    "risks": [
      {"risk_id": "R01", "name": "Toxic Leader", "severity": "high", "score": 0.9},
      {"risk_id": "R05", "name": "Psychological Safety Risk", "severity": "high", "score": 0.85}
    ]
  },
  "important_labels": [
    {"label_id": "M10-01", "name": "실행 추진", "confidence": 0.9}
  ]
}
```

---

## 9. 현재 시스템 이슈

### 9.1 미해결 과제

> **2026-04-23**: 모든 이슈 해결 완료

| # | 이슈 | 심각도 | 상태 |
|---|------|--------|------|
| 1 | **Label-Trait 미매핑** (60개) | High | **해결** |
| 2 | **LLM 확장 트리거 미연결** | Medium | **해결** |
| 3 | **Hybrid Trait 정의 부족** | Low | **해결** |

---

## 10. 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2026-04-23 | v1.0 | 초안 작성, Label-Trait Coverage 분석 포함 |
| 2026-04-23 | - | 통합 Trait Percentages 시스템 구현 (긍정+부정 통합) |
| 2026-04-23 | - | Partial Match 지원 (50% threshold) 추가 |
| 2026-04-23 | - | type 필드 추가 (positive/negative 구분) |
| 2026-04-23 | - | Trait ID 번호 체계 변경: Positive T01~T14, Negative T101~T106 |
| 2026-04-23 | - | Negative Traits新增: T104~T106 (Narcissistic, Manipulative, Volatile) |
| 2026-04-23 | - | Positive Traits新增: T13 (Ethical Courageous), T14 (Learning Agile) |
| 2026-04-23 | - | Label-Trait Coverage 100% 달성 |

---

## 11.附录

### 11.1 파일 목록

```
leadership/
├── src/
│   ├── leadership_engine.py     # Trait 추론 엔진
│   ├── nlp_pipeline.py          # LLM 파이프라인
│   └── ...
├── data/
│   ├── traits/
│   │   └── trait_definitions.json    # Trait 정의 (18개)
│   ├── micro_labels/
│   │   ├── positive_micro_labels.json  # 긍정 Label (67개)
│   │   └── negative_micro_labels.json  # 부정 Label (58개)
│   └── engine/
│       ├── hybrid_rules.json    # Hybrid Trait 규칙
│       ├── negative_mapping_rules.json
│       └── ...
└── docs/
    └── leadership_trait_system.md  # 본 문서
```

### 11.2 관련 문서

- `STRUCTURE.md`: 시스템 전체 구조
- `docs/architecture.md`: 아키텍처 상세
- `meta.md`: 메타데이터 정의