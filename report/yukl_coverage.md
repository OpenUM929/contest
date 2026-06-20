# Yukl 행동 커버리지 매트릭스 (내용 타당도)

> 2026-06-20 · Yukl·Gordon·Taber(2002)의 4 메타범주 × 12 구체 행동을 우리 trait/micro와 대조해 **내용 타당도(빠짐 없는가)**를 점검. 출처: [Yukl et al. 2002](https://journals.sagepub.com/doi/10.1177/107179190200900102) (doi:10.1177/107179190200900102).

## 매트릭스

| 메타범주 | Yukl 행동 | 우리 trait | 핵심 micro | 커버 |
|---|---|---|---|---|
| **Task** | clarifying(명확화) | T01·T06 (Initiating Structure) | M01-01, M06-01 | ✅ |
| Task | planning(계획) | T01·T10 | M06-01, M27-01 | ✅ |
| Task | monitoring(점검) | T05(역량)·T06 | M34-01, M10-02 | ✅ |
| **Relations** | supporting(지원) | T11 (Empathetic/Servant) | M12-01, M29-01 | ✅ |
| Relations | developing(육성) | T07 (Coaching/Servant) | M02-02, M07-02 | ✅ |
| Relations | recognizing(인정) | △ 부분 (T07 일부) | M02-03 | ⚠️ **갭** |
| Relations | empowering(임파워먼트) | **T15 (신설)** | M49-01, M49-02 | ✅ *(v5 보강)* |
| Relations | consulting(협의) | T02 (Participative) | M11-01, M15-03 | ✅ |
| **Change** | visioning(비전) | T09 (Visionary) | M01-04 | ✅ |
| Change | innovating(혁신) | T03 (Innovative) | M03-03, M23-01 | ✅ |
| Change | risk-taking(위험감수) | T03 | M22-02, M05-02 | ✅ |
| **External** | scanning(외부탐색) | △ 부분 (M43-03 in T09 optional) | M43-03, M16-01 | ⚠️ **갭** |

## 커버리지 요약
- **10 / 12 행동 커버** (83%, 목표 ≥80% 충족).
- **남은 2 갭**:
  1. **recognizing(건설적 인정·보상)** — 거래적 Contingent Reward의 긍정 짝. 현재 micro 산발(M02-03), 독립 trait 없음. → *Recognizing micro/trait 보강 후보* (레지스트리 transactional `add`와 일치).
  2. **scanning(외부탐색·경계관리)** — Yukl External 메타범주. M43-03(외부네트워킹)·M16-01(이해관계자)이 T09 optional에 산발할 뿐 독립 trait 없음. → *External/Boundary-spanning trait 신설 후보*.

## 메타범주별 균형
| 메타범주 | 커버 행동 | 상태 |
|---|---|---|
| Task | 3/3 | ✅ 견고 |
| Relations | 4/5 (recognizing 갭) | ✅ 임파워먼트 보강으로 강화 |
| Change | 3/3 | ✅ 견고 |
| External | 0.5/1 (scanning 갭) | ⚠️ 가장 약한 범주 |

> 결론: Task·Change·Relations는 내용 타당도 충족. **External(외부지향)이 구조적 최대 공백** — 상위 리더 진단 확장 시 1순위. recognizing은 거래적 보상 보강과 함께 처리.
> 갱신: trait/micro 변경 시 본 매트릭스 동기화. 빠짐 점검은 이 표 + `coverage_audit.py`(부모 커버리지) 병행.
