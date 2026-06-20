# Trait 과호출(over-firing) 구조 감사

> 순수 구조 분석. '한 입력에 여러 trait이 켜지는' 원인 = micro 신호 공유.
> 정밀 호출의 열쇠: trait마다 **고유 앵커(unique required)** 확보 + 공유 hub 가중치 하향.

## 1. Hub micro — 여러 trait에 걸친 라벨 (과호출의 원천)

fan-out = 이 micro가 구성요소로 들어간 trait 수. 높을수록 이 라벨 하나가 여러 trait을 켠다.

| micro | 이름 | fan-out | 소속 trait |
|-------|------|---------|-----------|
| M10-01 | 실행력 및 완수 | **4** | T01, T04, T06, T10 |
| M19-01 | 신속한 의사결정 | **4** | T01, T04, T06, T10 |
| M01-01 | 명확한 비전 제시 | **3** | T01, T09, T10 |
| M12-01 | 공감 및 감정적 배려 | **3** | T02, T08, T11 |
| M12-02 | 감정적 지지 | **3** | T02, T08, T11 |

## 2. required 공유 — 여러 trait의 '필수'에 동시에 박힌 라벨

이 라벨이 탐지되면 **여러 trait이 동시에 필수조건을 충족**받는다 → 가장 직접적인 과호출 원인.

| micro | 이름 | 필수인 trait |
|-------|------|-------------|
| M10-01 | 실행력 및 완수 | T01(Strategic Decisive Leader), T04(Crisis Manager), T06(Execution Driver), T10(Strategic Execution Leader) |
| M01-01 | 명확한 비전 제시 | T01(Strategic Decisive Leader), T09(Visionary Leader), T10(Strategic Execution Leader) |
| M11-01 | 적극적 경청 | T02(Collaborative Leader), T08(Emotional Intelligence Leader) |
| M19-01 | 신속한 의사결정 | T04(Crisis Manager), T06(Execution Driver) |
| M10-02 | 목표 지향 실행 | T06(Execution Driver), T10(Strategic Execution Leader) |
| M12-01 | 공감 및 감정적 배려 | T08(Emotional Intelligence Leader), T11(Empathetic Leader) |
| M14-01 | 타인 우선 행동 | T08(Emotional Intelligence Leader), T11(Empathetic Leader) |

## 3. Trait 쌍 시그니처 중첩 (Jaccard) — 사실상 중복

두 trait의 (required+optional) 집합이 얼마나 겹치나. 높으면 같은 증거에 둘 다 켜진다.

| trait A | trait B | 공유 | Jaccard |
|---------|---------|------|---------|
| T06 Execution Driver | T10 Strategic Execution Leader | 4개 | **0.67** |
| T08 Emotional Intelligence Leader | T11 Empathetic Leader | 4개 | **0.50** |
| T01 Strategic Decisive Leader | T10 Strategic Execution Leader | 4개 | **0.44** |
| T02 Collaborative Leader | T11 Empathetic Leader | 5개 | **0.38** |
| T04 Crisis Manager | T06 Execution Driver | 2개 | **0.29** |
| T02 Collaborative Leader | T08 Emotional Intelligence Leader | 3개 | **0.23** |
| T01 Strategic Decisive Leader | T06 Execution Driver | 2개 | **0.22** |
| T04 Crisis Manager | T10 Strategic Execution Leader | 2개 | **0.22** |
| T01 Strategic Decisive Leader | T04 Crisis Manager | 2개 | **0.20** |
| T01 Strategic Decisive Leader | T09 Visionary Leader | 2개 | **0.18** |
| T09 Visionary Leader | T10 Strategic Execution Leader | 1개 | **0.09** |
| T05 Analytical Leader | T13 Ethical Courageous Leader | 1개 | **0.08** |
| T07 Coaching Leader | T09 Visionary Leader | 1개 | **0.08** |
| T102 Risk: Authoritarian | T105 Risk: Manipulative Leadership | 2개 | **0.08** |
| T101 Risk: Avoidant | T106 Risk: Volatile Leadership | 1개 | **0.06** |

## 4. 앵커 없는 trait — 고유 필수 라벨이 없어 정밀 호출 불가

앵커 = 그 trait에만 있는(fan-out=1) required 라벨. 앵커가 없으면 이 trait은
**공유 라벨만으로 호출**되어 다른 trait과 항상 같이 켜진다.

| trait | 고유필수(앵커) | 고유선택 | 시그니처 | 진단 |
|-------|--------------|---------|---------|------|
| T01 Strategic Decisive Leader | 0 (없음) | 2 | 7 | ⚠️ 앵커없음 |
| T02 Collaborative Leader | 1 (M15-03) | 4 | 11 | ✅ 앵커있음 |
| T03 Innovative Leader | 3 (M03-03, M05-02, M23-01) | 6 | 9 | ✅ 앵커있음 |
| T04 Crisis Manager | 1 (M20-01) | 2 | 5 | ✅ 앵커있음 |
| T05 Analytical Leader | 1 (M34-01) | 2 | 4 | ✅ 앵커있음 |
| T06 Execution Driver | 0 (없음) | 0 | 4 | ⚠️ 앵커없음 |
| T07 Coaching Leader | 2 (M02-02, M07-02) | 4 | 7 | ✅ 앵커있음 |
| T08 Emotional Intelligence Leader | 0 (없음) | 0 | 5 | ⚠️ 앵커없음 |
| T09 Visionary Leader | 1 (M01-04) | 2 | 6 | ✅ 앵커있음 |
| T10 Strategic Execution Leader | 0 (없음) | 0 | 6 | ⚠️ 앵커없음 |
| T11 Empathetic Leader | 0 (없음) | 0 | 7 | ⚠️ 앵커없음 |
| T12 Balanced Leader | 2 (M28-01, M24-01) | 2 | 4 | ✅ 앵커있음 |
| T101 Risk: Avoidant | 2 (N08-02, N08-01) | 5 | 9 | ✅ 앵커있음 |
| T102 Risk: Authoritarian | 2 (N15-03, N19-01) | 13 | 18 | ✅ 앵커있음 |
| T103 Risk: Integrity Violation | 3 (N28-01, N34-01, N30-01) | 3 | 6 | ✅ 앵커있음 |
| T13 Ethical Courageous Leader | 3 (M33-01, M30-01, M33-02) | 5 | 9 | ✅ 앵커있음 |
| T14 Learning Agile Leader | 2 (M21-01, M22-01) | 5 | 7 | ✅ 앵커있음 |
| T104 Risk: Narcissistic Leadership | 2 (N04-01, N09-01) | 9 | 13 | ✅ 앵커있음 |
| T105 Risk: Manipulative Leadership | 2 (N02-03, N02-02) | 3 | 8 | ✅ 앵커있음 |
| T106 Risk: Volatile Leadership | 1 (N17-01) | 7 | 10 | ✅ 앵커있음 |

## 5. 향후 추가를 위한 설계 원칙

1. **앵커 우선**: 신규 trait은 fan-out=1 짜리 고유 필수 라벨(앵커)을 최소 1개 선언.
2. **역할 명시**: 신규 micro에 `role: discriminative|supporting` 부여 — 공유 hub는 supporting으로 가중치↓.
3. **추가만, 재번호 금지**: 라벨/ trait ID는 append-only. 폐기는 `deprecated:true`로 표시(삭제 X) → 과거 데이터 호환.
4. **호출 점수**: trait 점수 = Σ(앵커 가중치 高 + supporting 가중치 低). hub만으로는 임계 못 넘게.