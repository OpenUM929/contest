# RAG 인사검증 시스템 마스터 계획서

> 최초 작성: 2026-05-29 | 최종 업데이트: 2026-05-29  
> 버전: v2.0 (Phase 1·2 완료 반영)

---

## 현재 상태 (2026-05-29 기준)

| 항목 | 이전 (v2.1) | 현재 (v3.0) | 변화 |
|------|------------|------------|------|
| 마이크로레이블 | 178개 | 178개 | - |
| 벡터 수 | 178개 (1벡터/레이블) | **534개** (3벡터/레이블) | +3× |
| 샘플 인덱스 | 없음 | **+3,560개** (레이블당 20개) | 신규 |
| definition 완성도 | 97.5% (3개 누락) | **100%** | +3개 수정 |
| 과거시제 제외 로직 | 부정 레이블만 | **긍정+부정 전체** | 긍정 67개 추가 |
| 중복 키 오류 | T14 중복 (C2) | **수정 완료** | - |
| 미등록 트레이트 매핑 | T10, T11 없음 (C3) | **수정 완료** | +2개 |
| 조건부 쿼리 확장 | 항상 확장 | **신뢰도 <0.65 시만** | 정밀도↑ |
| 부정어 분류 | 2단계 | **3단계 (critical/soft/none)** | LLM 호출↓ |

---

## 완료된 작업

### ✅ Phase 1 — 데이터 품질 수정

| ID | 작업 | 결과 |
|----|------|------|
| 1.1 | M14-01, M14-02, M15-06 `definition` 추가 | `positive_micro_labels.json` 수정 |
| 1.2 | `context_rules.json` T14 중복 키 제거 | innovation 섹션 38~43번째 줄 수정 |
| 1.3 | `negative_mapping_rules.json` T10, T11 매핑 추가 | trait_negative_rules 배열에 2항목 추가 |
| 1.4 | M08-02↔M09-01, M12-03↔M15-01 경계 재정의 | when/not_when 적용 맥락 분리 |
| 1.5 | N09-01↔N14-02 경계 재정의 + N14-02 레이블명 분리 | "공로 독점" → "공로 가로채기" |
| 1.6 | 긍정 레이블 67개 `not_when` 과거시제 제외 일괄 추가 | `scripts/add_past_tense_exclusion.py` 실행 |
| 1.7 | M17-01, M24-01, M30-01 단문 definition 확장 | 10~22자 → 50자 이상 |
| 1.8 | M19-01↔N19-01, M05-02↔N05-02 경계 보강 | 준비도 기준 및 의견수렴 여부 명시 |

### ✅ Phase 2 — 벡터 DB 청크 구조 개선

| ID | 작업 | 결과 |
|----|------|------|
| 2.1 | `build_vector_db.py` 다중 벡터 생성 (정의/상황/통합) | `build_label_vectors()` 함수 신규 구현 |
| 2.2 | `vector_search.py` label_id별 최고 신뢰도 병합 | `search()` 메서드 교체 |
| 2.3 | 학습 샘플 보조 인덱스 빌더 | `load_training_samples()` 추가 |
| 2.4 | 보조 인덱스 통합 검색 | `_search_sample_index()` + `search()` 병합 |
| 2.5 | 신뢰도 기반 조건부 쿼리 확장 | `search_with_threshold()` 개선 |
| 2.6 | 부정어 심각도 3단계 분류 | `check_adversative_particles()` 교체 |

---

## 다음 단계 계획

---

### ⭐ Phase 0 (선행·핵심) — 평가 데이터셋 골드 구축

> **이 시스템의 천장을 결정하는 단계.** 분류기는 골드(정답 데이터)보다 정확할 수 없다. 따라서 *"다면평가를 얼마나 제대로 micro 라벨로 분류해 평가셋을 만드냐"* 가 95% 달성·RAG 강화·인사평가 방어가능성 *전부*의 전제다.
> **작업 표준서: [`report/GOLD_LABELING_PROTOCOL.md`](report/GOLD_LABELING_PROTOCOL.md)** — 라벨링 매뉴얼·AI 출력양식·κ 검증절차.

**왜 핵심인가**: 인사평가 용도(처장 결재 조건)에서 골드가 틀리면 무고한 관리자에게 "독성·학대 리더" 라벨 → 분쟁. 그래서 골드 품질을 *주장이 아니라 κ 수치로 증명*해야 한다.

**불변 원칙(타협 불가)**
1. **순환 금지**: AI가 만든 골드를 같은 AI가 평가받으면 무의미 → 골드는 **AI 1차 + 인간 adjudication**, 신뢰성은 **κ≥0.7**로 증명.
2. **누수 금지**: 골드를 **강화풀(벡터DB 적재) / 검증 홀드아웃**으로 분할. **95%는 홀드아웃에서만** 측정(강화풀로 재면 자기참조 가짜).
3. **맥락 보존**: 문장 간 의도(현 0%)는 단문이 아니라 **다문장 span** 단위로 라벨링.
4. **감사 가능**: AI 라벨마다 근거구간+사유+신뢰도. 멀티라벨·기권 허용(강제 금지).
5. **층화 보고**: "전체 95%"가 아니라 **난이도별(역접·부정·문장간·리스크) 정확도** 보고.

**파이프라인**: 다면평가 → 비식별화(PIA) → 단위분할(문장+맥락창) → AI 1차(멀티패스) → 다중라벨러 κ → (κ<0.7이면 정의수정·재라벨) → 인간 adjudication → 강화풀/홀드아웃 분할.

**산출물**: 골드 JSON(스키마는 프로토콜 §3), 층화 정확도 리포트, κ 리포트.

> ⚠️ **기획서 현행화 주의**: 본 계획서는 v2.0/v3.0(178라벨·14trait) 기준이나, 현재 taxonomy는 **v5(22 trait·180 micro·앵커게이트·T15 Empowering·T107 Abusive)** 로 갱신됨([`report/`](report/) 근거자료군 참조). Phase 3-B의 "T15=Strategic Thinker" 제안은 폐기(T15는 Empowering으로 신설됨). 골드 라벨링은 **v5 라벨 정의** 기준으로 수행할 것.

---

### Phase 3 — 미편입 레이블 31개 트레이트 통합

**목적:** enhanced 파일에는 있으나 `trait_definitions.json`의 어떤 트레이트에도 배정되지 않은 31개 긍정 레이블을 활성화한다.  
**파일:** `data/traits/trait_definitions.json`

#### 3-A. 기존 트레이트에 optional 배정 (즉시 가능)

기존 트레이트 구조를 유지하면서 `optional` 배열에 추가하는 방식. 리스크 없음.

| 레이블 ID | 레이블명 | 배정 트레이트 | 배정 유형 |
|----------|---------|------------|---------|
| M13-01 | 회복력 리더십 | T04 (위기관리) | optional |
| M16-01 | 이해관계자 관계 구축 | T02 (협업) | optional |
| M22-03 | 성찰/학습 지향 | T14 (학습 민첩성) | optional |
| M24-02 | 권한 위임 | T07 (코칭) | optional |
| M25-01 | 글로벌/다문화 리더십 | T08 (감성지능) | optional |
| M27-02 | 시간 관리 리더십 | T06 (실행) | optional |
| M29-01 | 팀 웰빙 케어 | T08 (감성지능) | optional |
| M38-01 | 경청과 공감 소통 | T08 (감성지능) | optional |
| M38-02 | 현재집중/경청 | T08 (감성지능) | optional |
| M39-01 | 인재 육성 및 승계 계획 | T07 (코칭) | optional |
| M40-01 | 예외 관리 (능동적) | T06 (실행) | optional |
| M40-02 | 조건부 보상 | T06 (실행) | optional |
| M41-01 | 자기인식 | T08 (감성지능) | optional |
| M41-02 | 균형적 정보처리 | T05 (분석) | optional |
| M42-01 | 직원 중심성 | T07 (코칭) | optional |
| M43-01 | 참여적 리더십 | T02 (협업) | optional |
| M43-02 | 조정/프로세스 관리 | T06 (실행) | optional |
| M43-03 | 외부 네트워킹/경계 확장 | T02 (협업) | optional |
| M44-01 | 정치적 인식 | T01 (전략적 결단) | optional |
| M44-02 | 성취지향 리더십 | T06 (실행) | optional |
| M45-01 | 환경 책임 의식 | T13 (윤리적 용기) | optional |
| M45-02 | 사회적 책임 리더십 | T13 (윤리적 용기) | optional |
| M46-01 | 선제적 주도성 | T03 (혁신) | optional |
| M46-02 | 기회 인식 | T03 (혁신) | optional |
| M47-01 | 공유 리더십 촉진 | T02 (협업) | optional |
| M47-02 | 효과적 추종 리더십 | T02 (협업) | optional |
| M48-01 | 자애적 리더십 | T07 (코칭) | optional |

#### 3-B. M36 시리즈 — 신규 트레이트 T15 추가 검토

M36 계열 4개(전략적 사고, 양손잡이 리더십, 의미 부여, 예지력)는 기존 트레이트와 성격이 달라 신규 트레이트 추가를 권장한다.

```json
{
  "trait_id": "T15",
  "trait_name": "Strategic Thinker",
  "trait_type": "positive",
  "description": "장기 전략적 사고와 미래 예측 능력을 갖춘 리더",
  "required": ["M36-01", "M36-04"],
  "optional": ["M36-02", "M36-03", "M01-02", "M01-04"],
  "hard_forbidden": ["N01", "N06"],
  "soft_forbidden": [{"label": "N19", "penalty": 0.3}],
  "context_weight": {"crisis": 1.0, "normal": 1.2, "innovation": 1.3},
  "hybrid_eligible": true,
  "k_trait": 1.1
}
```

#### 3-C. 부정 미편입 레이블 21개 (별도 검토)

N38~N43 시리즈(수동적 예외관리, 과신, 조직 비판, 비윤리적 관행 등)는 현재 부정 트레이트(T101~T106)와의 관계를 분석한 후 배정.

**구현 순서:**
1. `data/traits/trait_definitions.json`의 T01~T14 각 `optional` 배열에 3-A 항목 추가
2. T15 신규 트레이트 항목 추가
3. `data/engine/negative_mapping_rules.json`에 T15 매핑 추가
4. `scripts/validate_data.py` 실행으로 orphan 0개 확인

---

### Phase 4 — 벡터 DB 재빌드 및 성능 검증

**목적:** Phase 1~3 변경사항을 반영한 벡터 DB를 재빌드하고, 성능을 측정한다.

#### 4-1. 재빌드 실행

```bash
# enhanced 파일이 Phase 1 변경사항 반영했는지 먼저 확인
python scripts/validate_data.py

# 벡터 DB 재빌드 (약 3~5분 소요)
python build_vector_db.py
# 예상 출력:
# 총 534개 벡터 생성 (178개 레이블 × 최대 3벡터)
# 총 3,560개 샘플 로드 (178개 레이블)
```

#### 4-2. 성능 벤치마크

```bash
python scripts/benchmark.py
```

**목표 기준:**

| 지표 | 현재 추정 | 목표 |
|------|---------|------|
| Top-1 정확도 | ~55% | ≥ 70% |
| Recall@5 | ~70% | ≥ 90% |
| LLM 호출율 | ~60% | ≤ 40% |

#### 4-3. 5개 핵심 테스트 케이스 수동 검증

앱 실행(`python app.py`) 후 확인:

| 입력 | 기대 레이블 | 기대 트레이트 |
|------|-----------|------------|
| "문제가 발생하여 즉시 결단을 내렸다" | M19-01 | T04 |
| "약속했지만 실제로는 지키지 않았다" | N30-01, N02-01 | T105 |
| "데이터를 의도적으로 수정했다" | N34-01 | T103 |
| "의견을 충분히 들은 후 신속하게 결정했다" | M19-01 (긍정) | T04/T01 |
| "혼자서 바로 결정해버렸다. 팀 의견은 없었다" | N19-01 (부정) | T102 |

---

### Phase 5 — 시스템 안정성 개선

**목적:** 운영 환경에서의 안정성과 성능을 높인다.

#### 5-1. LLM 타임아웃 추가 (즉시)

**파일:** `src/nlp_pipeline.py` — `call_llm_with_retry()` 함수

```python
# 현재: 타임아웃 없음
response = client.chat.completions.create(...)

# 개선: 30초 타임아웃
response = client.chat.completions.create(
    ...,
    timeout=30.0
)
```

#### 5-2. 문장 가중치 LeadershipEngine 전달 (즉시)

**파일:** `app.py` — `/api/analyze` 엔드포인트  
현재 `apply_sentence_weights()`의 결과가 계산되지만 engine에 전달되지 않음.

```python
# 현재: 가중치 계산 후 버림
weighted = apply_sentence_weights(filtered)

# 개선: micro_labels 생성 시 가중치 반영
micro_labels = []
for sent in weighted:
    for lbl in sent['labels']:
        micro_labels.append({
            'label_id': lbl['label_id'],
            'confidence': lbl['confidence'] * sent.get('weight', 1.0),
            'context': sent.get('context', 'normal')
        })
```

#### 5-3. DB 인덱스 추가 (단기)

**파일:** `src/database.py` — `init_db()` 함수

```sql
-- 대시보드 쿼리 성능 개선
CREATE INDEX IF NOT EXISTS idx_analysis_created_at 
  ON analysis_results(created_at);
CREATE INDEX IF NOT EXISTS idx_analysis_user_id 
  ON analysis_results(user_id);
```

#### 5-4. enhanced 파일 ↔ 메인 파일 동기화 스크립트 (중기)

Phase 1에서 `positive_micro_labels.json`을 수정했으나 `positive_micro_labels_enhanced.json`의 일부 변경은 미동기화 상태. 양방향 diff 검증 스크립트 필요.

```bash
python scripts/sync_check.py  # 두 파일 간 definition/when/not_when 차이 리포트
```

---

### Phase 6 — 장기 아키텍처 개선 (선택)

| 항목 | 현재 | 개선 방향 | 시점 |
|------|------|---------|------|
| 벡터 인덱스 | FAISS (CPU) | pgvector 또는 Weaviate | 사용자 1,000명+ 시 |
| 메타데이터 저장 | JSON 파일 | PostgreSQL JSONB | 동시 사용자 10명+ 시 |
| LLM | OpenCode API | 파인튜닝 분류 모델 | 데이터 5만개+ 수집 후 |
| 피드백 루프 | 없음 | 인사담당자 검토 → 재학습 | Phase 5 완료 후 |

---

## 파일 구조 (현재)

```
C:\dev\leadership\
├── RAG_PLAN.md                    ← 이 파일 (마스터 계획서)
├── AGENTS.md                      ← 프로젝트 나침반
├── FILE_STRUCTURE.md              ← 파일 구조 참조
├── app.py                         ← Flask 메인 앱
├── build_vector_db.py             ← 벡터 DB 빌더 (v3.0 다중벡터)
├── scripts/
│   ├── validate_data.py           ← 데이터 정합성 검증
│   ├── benchmark.py               ← 검색 성능 벤치마크
│   └── add_past_tense_exclusion.py← 과거시제 제외 문구 일괄 추가
├── docs/
│   ├── IMPROVEMENT_GUIDE.md       ← Phase 1·2 구현 상세 가이드
│   ├── label_audit_report.md      ← v2.1 레이블 감사 보고서 (참조용)
│   ├── core.md                    ← 파이프라인 명세
│   ├── HANDOVER.md                ← 시스템 운영 가이드
│   └── ...
├── data/
│   ├── micro_labels/              ← 메인 레이블 정의 (수정됨)
│   ├── traits/trait_definitions.json ← 트레이트 정의 (Phase 3 대상)
│   ├── engine/                    ← 스코어링/컨텍스트 규칙 (수정됨)
│   └── vectors/                   ← 벡터 DB (Phase 4 재빌드 대상)
├── dataset/
│   ├── ori/                       ← Enhanced 레이블 + 학습 샘플
│   └── fixed_dataset.json         ← 수정된 샘플 데이터
└── src/
    ├── vector_search.py           ← 검색 모듈 (v3.0 개선됨)
    ├── leadership_engine.py       ← 트레이트 추론 엔진
    └── nlp_pipeline.py            ← LLM 파이프라인
```

---

## 즉시 실행 커맨드

```bash
# 1. 데이터 검증 (Phase 1 완료 확인)
python scripts/validate_data.py

# 2. 벡터 DB 재빌드 (Phase 2 적용)
python build_vector_db.py

# 3. 성능 벤치마크
python scripts/benchmark.py

# 4. 앱 실행
python app.py
```
