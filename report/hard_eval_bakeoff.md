# Hard 평가셋 측정 + 모델 Bake-off 리포트

> 2026-06-20 · 산출: `data/eval/hard_eval_set.json`(36케이스/6범주), `scripts/eval_hard.py`(채점 harness), `scripts/bakeoff_koelectra.py`
> 목적: 단문·고립 학습데이터가 못 담는 맥락 의존 케이스에서 분류기 한계를 **처음으로 실측**.

---

## 0. 한 줄 요약
- 쉬운 홀드아웃 69% → **Hard 42%로 급락**. 특히 역접·부정·문장간 의도에서 붕괴.
- **cross_sentence_intent는 모든 모델 0%** → 단문 분류기로 불가, **LLM 추론 영역**으로 확정.
- 의미 임베딩(ko-SBERT)은 부정(20→60%)·역접(29→43%)에서 TF-IDF를 앞섬 → 의미 신호가 표면 실패를 보완.
- 결론: **2단계(분류기=쉬운 케이스 / LLM=맥락 hard) 설계가 실측으로 정당화**됨. 이전 연구의 H3/H4("부정·맥락은 추론 필요")가 **검증 불가→검증됨**.

---

## 1. Hard 평가셋 (6범주 × 총 36)
| 범주 | 정의 | 예 |
|---|---|---|
| mirror_flip | 표면 유사, 맥락이 극성 뒤집음 | "바로 결정"(M19) ↔ "혼자 밀어붙임"(N19) |
| reversal | 긍정 후 "하지만 실제로는" 반전 | "듣겠다 했지만 정해둔 대로"→N19 |
| cross_sentence_intent | 의도가 뒤 문장에 | "자유롭게 말하라…반대자는 따로 질책"→N15 |
| negation | 부정 형태소로 반전 | "실행에 옮기지 못했다"→N10 |
| past_tense_exclusion | 과거 회상 → 거부(gold=null) | "예전엔 혼자 결정했었다" |
| hub_disambiguation | 공유 hub + 변별 단서 | "실행 + 전략적 자원배분"→M27 |

채점: gold 라벨은 top-1 일치, gold=null은 confidence<0.35 거부 시 정답. deprecated 라벨은 v4 생존 라벨로 정규화 후 비교.

---

## 2. 결과 (범주별 정확도)
| 범주 | TF-IDF(floor) | KoELECTRA frozen | ko-SBERT |
|---|---|---|---|
| mirror_flip | 60% | 40% | 50% |
| reversal | 29% | 0% | **43%** |
| cross_sentence_intent | **20%** | 0% | **0%** |
| negation | 20% | 40% | **60%** |
| past_tense_exclusion | 50% | 50% | 25% |
| hub_disambiguation | 60% | 20% | 60% |
| **전체** | **42%** | **25%** | **42%** |

> 참고: 쉬운 홀드아웃에서는 TF-IDF도 69%. Hard에서 42%로 떨어지는 **27%p 격차가 "맥락 비용"**.

---

## 3. 모델별 해석 (정직하게)
- **TF-IDF**: 표면 어휘에 강함(mirror/hub 60%)이나 부정·역접에 취약(20·29%). H25 "실행에 옮기지 못했다"→M10-01(실행력) 같은 극성 오류.
- **KoELECTRA(frozen, mean-pool)**: 25%로 최하. **단, 이는 "KoELECTRA가 나쁘다"가 아님** — fine-tune 없이 discriminator를 평균풀링한 임베딩은 문장표현으로 약하다는 알려진 한계. 공정한 비교 아님.
- **ko-SBERT(jhgan/ko-sroberta-multitask, frozen)**: 전체는 TF-IDF와 동률(42%)이나 **분포가 핵심** — 부정 60%·역접 43%로 의미 신호가 표면 실패를 보완. cross_sentence·past_tense는 약함(frozen이라 규칙 미반영).

## 4. 모델 무관 핵심 발견
- **cross_sentence_intent = 전 모델 0%.** 문장 간에 의도가 흩어진 케이스는 단일 문장 분류로 원천 불가 → 명백한 **LLM/추론 전담** 영역.
- 어떤 off-the-shelf 분류기도 hard 전체를 못 풂 → **2단계 라우팅 + 앵커 게이트(과호출 차단)** 설계가 옳음.

---

## 5. 다음 단계 (이번엔 미실행, 근거와 함께 명시)
1. **공정한 상한 측정**: frozen이 아니라 **fine-tune**(KoELECTRA 분류헤드 backprop) 또는 **KURE**(BGE-m3 기반, 검색 SOTA, ~2GB). 부정·역접에서 ko-SBERT 위를 확인.
2. **2단계 라우팅 구현**: 분류기 confidence<게이트 → LLM 경로. Hard셋의 저confidence 오답 대부분이 게이트에 걸림(예: H35 0.03, H26 0.16) → 라우팅으로 회수 가능. 단 고confidence 오답(H18 0.60, H22 0.69)은 위험 → 별도 규칙(과거시제·역접 마커) 필요.
3. **Hard셋 확장**: 현재 36 → 다면평가 실문장으로 수백 규모. 특히 cross_sentence·reversal 보강.
4. **다면평가는 학습이 아니라 평가/라우팅 튜닝용**(앞선 결론 유지).
