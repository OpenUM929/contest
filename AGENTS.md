# AGENTS.md - Leadership Label Vector DB Project

> **Project Compass**  
> 이 문서는 프로젝트의 중앙 나침반입니다. 어떤 파일이 어디에 있고 무엇을 하는지, 그리고 현재 상태는 어떤지 한눈에 파악할 수 있습니다.  
> **버전:** v2.1 | **라벨:** 178개 | **샘플:** 12,460개 | **마지막 업데이트:** 2026-05-18

---

## 현재 상태

| 항목 | 수치 | 상태 |
|------|------|------|
| 총 라벨 | 178개 (Positive 98 + Negative 80) | ✅ 완료 |
| 학습 샘플 | 12,460개 (라벨당 70개) | ✅ 완료 |
| Vector DB | 178 vectors (KoE5, 768-dim) | ✅ 완료 |
| 중복 텍스트 | 0개 | ✅ 완료 |
| 배치 파일 | 18개 | ✅ 완료 |
| 통합 파일 | `training_data_all_labels.json` | ✅ 완료 |

---

## 문서 지도

어떤 정보를 찾고 계신가요? 아래 표를 참조하세요.

| 찾는 정보 | 문서 위치 | 설명 |
|-----------|-----------|------|
| **파일 구조, 라벨 계층도, 배치 매핑** | [FILE_STRUCTURE.md](FILE_STRUCTURE.md) | 전체 디렉토리 트리, Macro→Micro 관계도, 18개 배치 ↔ 라벨 ID 매핑표, JSON 스키마 |
| **파이프라인 상세 명세** | [docs/core.md](docs/core.md) | Vector DB → LLM → Trait 추론 흐름, 컴포넌트 명세, 임계값 설정, API 응답 포맷 |
| **시스템 운영 방법** | [docs/HANDOVER.md](docs/HANDOVER.md) | 웹 서버 실행, 데이터 수정 워크플로우, API 엔드포인트, 해결된 이슈, 남은 과제 |
| **Vector DB + LLM 설계 계획** | [docs/vector_db_vs_llm_plan.md](docs/vector_db_vs_llm_plan.md) | 아키텍처 비교, 실패 사례 분석(T04-B, T105-A), 개발 결과, 성능 지표 |
| **웹 수정 시스템 계획** | [docs/WEB_EDIT_PLAN.md](docs/WEB_EDIT_PLAN.md) | 웹 기반 라벨/트레이트 편집, 통합 파일 생성, 백업 시스템 |
| **라벨 감사 보고서** | [label_audit_report.md](label_audit_report.md) | 178개 라벨의 정의, when/not_when, 예시 문장 |
| **학술 타당성 검토** | [report/taxonomy_academic_review.md](report/taxonomy_academic_review.md) | trait/micro를 리더십 이론(Yukl·FRLM·Schmidt·메타분석)과 대조, 분석수준 혼재·중복 진단 |
| **⭐ 근거 백서(처음 읽기)** | [report/WHITEPAPER.md](report/WHITEPAPER.md) | 초급자·비전문가용 설득 문서: '왜 믿어도 되는가'를 비유·용어사전과 함께 |
| **근거 자료(리더십 유형별)** | [report/INDEX.md](report/INDEX.md) | 구성개념별 trait↔micro 연계 + 출처 링크(각각), [FACT_CHECK](report/FACT_CHECK.md) |
| **인과관계 형성 리포트** | [report/CAUSAL_REPORT.md](report/CAUSAL_REPORT.md) | 구성개념→trait→micro 인과를 *어떤 원리로 형성했는가*(6원리·신뢰도계층·검증법) |
| **Yukl 커버리지 매트릭스** | [report/yukl_coverage.md](report/yukl_coverage.md) | 12행동 내용타당도 10/12, 갭=recognizing·external. trait_kind·v5(22 trait) 반영 |
| **출처·근거 강화 방법** | [report/SOURCE_RIGOR_PLAN.md](report/SOURCE_RIGOR_PLAN.md) | 정당성 ↑ 10방법(M1~M10). 진단 `source_rigor_audit.py`, 척도대응 `scale_item_map.json` |
| **매핑 코드북(재현성)** | [report/CODEBOOK.md](report/CODEBOOK.md) | 구성개념→trait→micro 코딩 규칙(R-A/B/C) + 2차 독립코딩 κ 절차 |
| **⭐ 골드 라벨링 표준서** | [report/GOLD_LABELING_PROTOCOL.md](report/GOLD_LABELING_PROTOCOL.md) | 평가 데이터셋 구축의 핵심: 비식별화→AI 1차→κ→인간 adjudication→강화/홀드아웃 분할 |
| **자료 전문성·근거 평가** | [report/MATERIALS_ASSESSMENT.md](report/MATERIALS_ASSESSMENT.md) | 자기평가(보수적): 메타층 강·대상층 부정편중·데이터층 공백. 종합 ~3.0/5 |
| **근거 품질 개선 계획** | [report/IMPROVEMENT_PLAN.md](report/IMPROVEMENT_PLAN.md) | 조사로 가능한 4차원 개선(출처·근거·인과·구성타당도) 4 Phase·합격기준·목표점수 |
| **증거 추세 추적** | [report/evidence_tracking.md](report/evidence_tracking.md) | 학술 위상의 시대별 추세·갱신 루프. 원천: `data/evidence/leadership_evidence_registry.json` |
| **확장 워크플로(게이트)** | [report/taxonomy_extension_workflow.md](report/taxonomy_extension_workflow.md) | 새 라벨/trait 추가 절차 + 불변식 게이트 `scripts/validate_taxonomy.py` |
| **분석 알고리즘 참고 모델** | [report/algorithm_models.md](report/algorithm_models.md) | KoE5·big-pickle(프로덕션) + TF-IDF·KoELECTRA·ko-SBERT·KURE(실험) 모델 정보·출처 |

---

## 데이터 지도

프로젝트의 핵심 데이터 파일과 그 역할입니다.

### 라벨 정의 (수정 시 주의)

| 파일 | 위치 | 역할 | 의존성 |
|------|------|------|--------|
| `positive_micro_labels_enhanced.json` | `dataset/ori/` | 98개 긍정 라벨 정의 (벡터DB 유일 소스) | `build_vector_db.py`가 직접 읽음 |
| `negative_micro_labels_enhanced.json` | `dataset/ori/` | 80개 부정 라벨 정의 (벡터DB 유일 소스) | `build_vector_db.py`가 직접 읽음 |
| `positive_labels.json` | `data/labels/` | 48개 긍정 매크로 카테고리 | 매크로 분류용 |
| `negative_labels.json` | `data/labels/` | 32개 부정 매크로 카테고리 | 매크로 분류용 |

### 학습 데이터

| 파일 | 위치 | 역할 | 생성 방법 |
|------|------|------|-----------|
| `batch1~20.json` | `dataset/ori/` | 18개 배치 파일 (12,460개 샘플) | AI 생성 후 품질 검증 |
| `training_data_all_labels.json` | `dataset/ori/` | 18개 배치 통합 마스터 파일 | `batch*.json` 단순 병합 |

### Vector DB 산출물

| 파일 | 위치 | 역할 | 재생성 방법 |
|------|------|------|-------------|
| `label_vectors.faiss` | `data/vectors/` | FAISS 인덱스 (178 vectors) | `python build_vector_db.py` |
| `metadata.json` | `data/vectors/` | 라벨 ID/텍스트 메타데이터 | `python build_vector_db.py` |
| `test_results.json` | `data/vectors/` | T04-B, T105-A 테스트 결과 | `python build_vector_db.py` |

### 핵심 스크립트

| 파일 | 위치 | 역할 |
|------|------|------|
| `app.py` | 루트 | Flask 웹 서버 (분석 API + 라벨/트레이트 수정 UI) |
| `build_vector_db.py` | 루트 | KoE5 임베딩 → FAISS 인덱스 생성 (178개 라벨 대상) |

---

## 품질 기준

모든 배치 데이터는 다음 기준을 충족해야 합니다.

- **문장 길이:** 20-120자
- **중복:** 0개 (모든 텍스트 고유)
- **라벨당 샘플:** 정확히 70개 (clean 50 + hard_negative 20)
- **스타일 분포:** 4가지 균등 (`direct_speech`, `indirect_report`, `scene_description`, `euphemism`)
- **플레이스홀더:** 금지 (`~`, `[content]`, `{content}`)
- **Hard Negative:** 표면적으로 유사하나 `not_when` 조건을 실제로 위반하는 문장

---

## 빠른 시작

### 1. 웹 서버 실행
```bash
cd C:\dev\leadership
python app.py
# http://localhost:5000
```

### 2. Vector DB 재구축
```bash
python build_vector_db.py
```

### 3. 배치 데이터 검증
```bash
python -c "import json; d=json.load(open('dataset/ori/training_data_all_labels.json')); print(f'Total: {len(d)}, Labels: {len(set(x[\"label_id\"] for x in d))}')"
```

### 4. 라벨 수정 → AI 검토
```
1. http://localhost:5000/edit/labels 접속
2. 라벨 수정 후 저장 (자동 백업)
3. [AI 검토용 통합] 버튼 클릭
4. AI에게 "temp/integrated_data.json 읽고 검토해줘" 요청
```

---

## 버전 역사

### v2.1 (2026-05-18) — Current
- 178개 라벨 완성 (98 긍정 + 80 부정)
- 12,460개 고품질 학습 샘플 생성
- Vector DB 178 vectors로 재구축
- 18개 배치 파일 표준화, 중복 제거
- FILE_STRUCTURE.md 신규 작성
- AGENTS.md 나침반 역할로 개편

### v2.0 (2026-04-30)
- 54개 신규 마이크로 라벨 추가 (31 긍정 + 23 부정)
- 웹 기반 라벨/트레이트 수정 시스템 구축
- 개별 마이크로 라벨 JSON 파일 생성

### v1.0
- 98개 긍정 + 27개 부정 라벨
- 초기 Vector DB 구축

---

## 문제 해결

| 증상 | 원인 | 해결책 | 참고 문서 |
|------|------|--------|-----------|
| Vector DB 검색 실패 | 인덱스 손상/불일치 | `python build_vector_db.py` 재실행 | [docs/core.md](docs/core.md) #8 |
| 라벨 스키마 오류 | enhanced JSON 로드 실패 | `dataset/ori/*_enhanced.json` 경로 확인 | [FILE_STRUCTURE.md](FILE_STRUCTURE.md) |
| LLM JSON 파싱 오류 | 코드블록 포함 출력 | 프롬프트에 "순수 JSON만" 강화 | [docs/core.md](docs/core.md) #8 |
| 웹 수정 저장 실패 | 개별 파일 권한 | 백업 폴더 `data/*/backups/` 확인 | [docs/HANDOVER.md](docs/HANDOVER.md) #4 |

---

## 근거 자료 & 모델 사용 지침 (언제 참고 / 언제 구현)

> trait/micro의 학술 근거 문서를 **언제 참고하고 언제 구현에 반영하는지**의 규칙. 근거 없는 추가/과증식을 막는다.

### 언제 *참고*(reference) 하나
- 새 trait·micro를 **기획/제안**할 때 → `report/INDEX.md`(유형별 trait↔micro+출처), `report/taxonomy_academic_review.md`(이론 대조)
- 기존 정의를 **검토/리뷰**할 때 → `report/FACT_CHECK.md`(출처 링크로 사실확인)
- 분석 **결과의 학술적 신뢰도/시의성**을 표기할 때 → `data/evidence/leadership_evidence_registry.json`의 위상(status/trend)
- 추출 **모델을 고를** 때 → `report/algorithm_models.md`

### 언제 *구현*(implement) 하나 — 게이트
구현(엔진/taxonomy 반영)은 **아래를 모두 충족할 때만**:
1. 레지스트리 `implication = add`(또는 merge/deprecate) 이고 **FACT_CHECK 확인 완료**
2. `validity_status`가 `contested/redundant`가 **아님** (이 경우 신설 금지 → 흡수). 예: 진성·윤리(T13)는 신설 아님
3. `out_of_scope`(예: 공유/분산=팀수준)는 구현 대상 아님
4. **'X특화 리더십'(green 등)은 trait이 아니라 context 차원으로** 흡수
5. `scripts/validate_taxonomy.py` 불변식 통과(앵커≥1·orphan=0 등)
6. 가능하면 평가 데이터로 검증 후 반영(다면평가는 학습 아닌 평가/튜닝용)

### 언제 *갱신* 하나
- `evidence_trends.py`가 `next_review_due`(6개월) 경보 또는 새 메타분석 인지 시 → 레지스트리 수정 → `gen_evidence_docs.py` 재생성 → `evidence_trends.py` 신호 재확인 (루프: `report/evidence_tracking.md`)

### 현재 backlog 요약(2026-06-20)
- **구현 후보(add)**: 서번트(T07·T11 통합)·임파워링(신설)·학대적감독(부정 신설)·거래적보상(보강)
- **흡수(merge/watch)**: 적응형→change축, 진성·윤리→변혁축, 겸손·포용→관계축, green→context(sustainability)
- **범위 밖**: 공유/분산

---

## 중요 규칙

1. **Vector DB 소스:** 반드시 `dataset/ori/*_enhanced.json`만 사용. `data/micro_labels/`는 참조하지 않음.
2. **배치 수정:** 개별 `batch*.json` 수정 후 반드시 `training_data_all_labels.json`을 재생성할 것.
3. **문서 업데이트:** 파일 구조/라벨 변경 시 `FILE_STRUCTURE.md`와 `AGENTS.md`를 함께 갱신할 것.
4. **백업:** 라벨 수정 전 자동 백업이 생성되지만, 대규모 변경 전 수동 백업 권장.

---

> **이 문서를 처음 읽는다면:** [FILE_STRUCTURE.md](FILE_STRUCTURE.md) → [docs/core.md](docs/core.md) 순서로 읽는 것을 권장합니다.
