# 분석 알고리즘 · 참고 모델 정보

> 2026-06-20 · 리더십 분석 파이프라인이 사용/검토한 모델을 한 곳에 정리. 향후 개발 시 모델 선택 근거와 출처 링크로 사용.
> 관련: 성능 실측은 [hard_eval_bakeoff.md](hard_eval_bakeoff.md), 타당성 PoC는 [ai_feasibility_study.md](ai_feasibility_study.md).

---

## 0. 파이프라인 3단계와 모델 역할
```
입력 문장
 └─(Step1) Micro Label 추출  ← LLM(big-pickle) + Vector DB(KoE5) 후보검색
     └─(Step2) Trait 추론     ← LeadershipEngine(결정적 규칙, 학습모델 아님)
         └─(Step3) 결과/리스크 ← trait_definitions 조회
```
- **Step1(추출)**: 의미 임베딩/LLM이 담당 — *학습·모델 선택의 대상*.
- **Step2(조합)**: 규칙 엔진(앵커 게이트·required/optional/forbidden) — *모델 아님, 결정적*. [leadership_engine.py]
- 즉 "어떤 모델이냐"는 **Step1에만** 해당. 아래 표가 그 후보·실측.

---

## 1. 프로덕션 사용 모델

| 모델 | 유형 | 역할 | 차원/비고 | 출처 |
|---|---|---|---|---|
| **KoE5** (`nlpai-lab/KoE5`) | 한국어 문장 임베딩(E5 계열) | Vector DB(FAISS) 라벨 후보 검색 | 768-dim, 178 라벨 인덱싱 | https://huggingface.co/nlpai-lab/KoE5 |
| **big-pickle** (OpenCode Zen) | LLM(클라우드, 무료) | Step1 micro label 추출(프롬프트 기반) | base_url `opencode.ai/zen/v1` | https://opencode.ai |
| **LeadershipEngine** | 결정적 규칙 엔진 | Step2 trait 조합(앵커 게이트 포함) | 학습 모델 아님 | `src/leadership_engine.py` |

> 주의: 프로덕션 추출 신뢰도는 LLM 프롬프트 품질에 크게 의존. Vector DB(KoE5)는 후보 좁히기/일관성 보조.

---

## 2. 실험·Bake-off 모델 (Hard 평가셋 36케이스)

| 모델 | 유형 | Hard 전체 | 강점/약점 | 상태 | 출처 |
|---|---|---|---|---|---|
| **TF-IDF char_wb(2-5)+LogReg** | 표면 어휘(floor) | **42%** | mirror/hub 강(60%)·부정/역접 약(20·29%) | 기준선 | scikit-learn |
| **KoELECTRA** (`monologg/koelectra-base-v3-discriminator`) | 사전학습 인코더(frozen mean-pool) | 25% | frozen이라 문장표현 약 — *공정비교 아님* | 실험 | https://github.com/monologg/KoELECTRA |
| **ko-SBERT** (`jhgan/ko-sroberta-multitask`) | 문장 임베딩(SBERT) | **42%** | 부정 60%·역접 43%로 TF-IDF 상회 | 실험 | https://huggingface.co/jhgan/ko-sroberta-multitask |
| **KURE** (Korea Univ, BGE-m3 기반) | 검색 임베딩 SOTA | 미실행 | 공정 상한 측정 후보(~2GB) | 후보 | https://huggingface.co/nlpai-lab/KURE-v1 · https://huggingface.co/BAAI/bge-m3 |
| **KcELECTRA** (`beomi/KcELECTRA`) | 사전학습 인코더(2021, KOTE가 사용) | 참고 | 댓글 도메인 특화·다소 구버전 | 참고 | https://github.com/Beomi/KcELECTRA |

> 핵심 결론(상세 bake-off 문서): off-the-shelf 분류기는 hard 전체를 못 풂(특히 cross_sentence_intent 전 모델 0%) → **2단계 라우팅(쉬운=분류기 / 맥락=LLM) + 앵커 게이트** 설계가 정당.

---

## 3. 개념·방법론 참고 (모델 외)
| 항목 | 설명 | 출처 |
|---|---|---|
| **KOTE** | 한국어 감정 태깅(50라벨) — 경량 분류기 접근의 원형 | https://github.com/searle-j/KOTE |
| **앵커 게이트** | trait 고유 required 라벨 없으면 미점화 → 구조적 과호출 차단 | `docs/taxonomy_design.md` |
| **2단계 라우팅(계획)** | confidence<게이트 → LLM 경로; 고conf 오답은 규칙 보강 | `docs/hard_eval_bakeoff.md` §5 |

---

## 4. 모델 선택 지침 (향후 개발)
1. **Step2(조합)는 모델화하지 말 것** — 결정적 규칙 유지(해석가능·감사가능). 학술 근거는 trait 정의에 반영.
2. **Step1 추출 모델 교체 시**: 같은 Hard 평가셋(`data/eval/hard_eval_set.json`)+`scripts/eval_hard.py`로 동일 채점 후 비교. frozen mean-pool 수치는 모델 우열 근거로 쓰지 말 것(fine-tune 전제).
3. **공정 상한**은 KURE 또는 fine-tune로 측정(미실행, 다음 단계).
4. 평가 데이터 유입 후 라우팅 임계값 튜닝 — 학습이 아니라 평가/라우팅용으로 다면평가 사용(PII 처리).

---
_갱신 시 hard_eval_bakeoff.md 수치와 동기화. 모델 추가는 본 표 + bake-off 스크립트에 함께 반영._
