# RAG 인사검증 시스템 개선 가이드

> 작성일: 2026-05-29  
> 기반 문서: RAG_PLAN.md  
> 범위: 데이터 품질 수정 + 벡터 DB 청크 구조 개선

---

## Part 1. 데이터 품질 수정

---

### C1. [CRITICAL] definition 필드 누락 — M14-01, M14-02, M15-06

**파일:** `data/micro_labels/positive_micro_labels.json`

해당 3개 레이블의 `definition` 필드를 아래 내용으로 추가한다.

#### M14-01 — 타인 우선 행동

```json
"definition": "자신의 이익보다 타인의 필요를 먼저 고려하여 행동하는 것. 자원, 기회, 공로를 타인에게 먼저 양보하는 구체적 행동으로 드러남"
```

**before:**
```json
{
  "label_id": "M14-01",
  "label_name": "타인 우선 행동",
  "macro": "L14",
  "weight": 0.7,
  "when": "본인이 진정 손해/리스크 감수하고 타인을 위한 행동",
  "not_when": "단순 양보 제스처, 상호이익 거래, 보상 기대한 도움"
}
```

**after:**
```json
{
  "label_id": "M14-01",
  "label_name": "타인 우선 행동",
  "macro": "L14",
  "weight": 0.7,
  "definition": "자신의 이익보다 타인의 필요를 먼저 고려하여 행동하는 것. 자원, 기회, 공로를 타인에게 먼저 양보하는 구체적 행동으로 드러남",
  "when": "본인이 진정 손해/리스크 감수하고 타인을 위한 행동",
  "not_when": "단순 양보 제스처, 상호이익 거래, 보상 기대한 도움",
  "context_weight": { "crisis": 1.1, "normal": 1.2, "innovation": 1.0 }
}
```

#### M14-02 — 희생적 지원

```json
"definition": "팀원이나 조직을 위해 자신의 시간, 에너지, 자원을 희생하는 행동. 추가 보상 없이 타인의 성공을 위해 헌신하는 모습으로 나타남"
```

#### M15-06 — 심리적 보호

```json
"definition": "팀원이 외부 압력, 비난, 위험으로부터 안전하게 업무할 수 있도록 적극적으로 보호막 역할을 수행. 상위 조직의 부당한 요구를 차단하거나 팀원 대신 책임을 지는 행동 포함"
```

---

### C2. [CRITICAL] context_rules.json — T14 중복 키 제거

**파일:** `data/engine/context_rules.json` (38~43번째 줄)

**before:**
```json
"trait_multipliers": {
  "T14": 1.3,
  "T03": 1.3,
  "T14": 1.3,
  "T05": 1.3
}
```

**after:**
```json
"trait_multipliers": {
  "T14": 1.3,
  "T03": 1.3,
  "T05": 1.3
}
```

---

### C3. [CRITICAL] negative_mapping_rules.json — T10, T11 매핑 추가

**파일:** `data/engine/negative_mapping_rules.json`

`trait_negative_rules` 배열의 마지막 항목 뒤에 아래 두 항목을 추가한다.

```json
{
  "trait_id": "T10",
  "trait_name": "Strategic Execution Leader",
  "logic": "전략 실행형 리더는 책임 회피 및 실행력 저해와 충돌",
  "hard_forbidden": [
    "N10",
    "N08"
  ],
  "soft_forbidden": [
    { "label": "N06", "penalty": 0.3 },
    { "label": "N19", "penalty": 0.4 }
  ],
  "risk_amplifier": []
},
{
  "trait_id": "T11",
  "trait_name": "Empathetic Leader",
  "logic": "공감형 리더는 심리적 안전 파괴 및 정서적 착취와 충돌",
  "hard_forbidden": [
    "N12",
    "N14"
  ],
  "soft_forbidden": [
    { "label": "N15", "penalty": 0.5 },
    { "label": "N11", "penalty": 0.3 }
  ],
  "risk_amplifier": []
}
```

---

### H4~H6. [HIGH] 중복 레이블 쌍 경계 정의

#### H4. M08-02 ↔ M09-01 ("공정한 성과 인정" 중복)

**처리 방향:** `not_when` 조건으로 적용 맥락을 분리한다.

- **M08-02** → 개인 성과에 대한 직접 인정 (1:1 피드백, 공개 포상)
- **M09-01** → 팀 전체 성과에 대한 공정한 분배와 인정

**M08-02 수정:**
```json
"when": "개인 업무 결과에 대해 직접적으로 인정하고 칭찬하는 경우, 1:1 피드백 또는 공개 표창",
"not_when": "팀 전체 성과 분배 상황, 보상 시스템 설계 맥락, 과거 회상 서술"
```

**M09-01 수정:**
```json
"when": "팀 또는 프로젝트 성과를 구성원 기여도에 따라 공정하게 분배하고 인정하는 경우",
"not_when": "개인 단위 칭찬 및 즉각적 피드백 상황, 과거 회상 서술"
```

---

#### H5. M12-03 ↔ M15-01 ("심리적 안전감 조성" 중복)

- **M12-03** → 팀 내 갈등·실수 상황에서 심리적 안전감을 유지
- **M15-01** → 일상적 소통 환경에서 심리적 안전감을 만드는 구조 설계

**M12-03 수정:**
```json
"when": "갈등, 실수, 실패 상황에서 팀원이 책임을 두려워하지 않도록 보호하는 경우",
"not_when": "일상적 소통 환경 설계, 채널 개설, 제도 수립 맥락, 과거 회상 서술"
```

**M15-01 수정:**
```json
"when": "발언 채널 개설, 익명 피드백 도입, 열린 회의 문화 설계 등 구조적 안전감 조성",
"not_when": "갈등·사고 발생 직후 대응, 개인 실수에 대한 직접 보호, 과거 회상 서술"
```

---

#### H6. N09-01 ↔ N14-02 ("공로 독점" 중복)

- **N09-01** → 팀 성과를 자신의 것으로 독점하는 행동
- **N14-02** → 자기 이익을 위해 타인 기여를 의도적으로 축소·은폐

**N09-01 수정:**
```json
"when": "팀 또는 협업 성과를 상위 조직에 보고할 때 본인 기여만 부각하는 경우",
"not_when": "의도적 정보 조작, 특정 구성원 공로 삭제, 과거 회상 서술"
```

**N14-02 수정:**
```json
"when": "특정 구성원의 기여를 문서에서 삭제하거나, 보고 시 의도적으로 타인 공로를 축소하는 경우",
"not_when": "팀 전체 성과 보고 맥락, 무의식적 누락, 과거 회상 서술"
```

---

### M1. [MEDIUM] 모든 긍정 레이블에 과거시제 제외 문구 추가

부정 레이블에는 이미 과거 시제 제외 규칙이 있으나 긍정 레이블에는 없다.  
`positive_micro_labels.json`의 모든 레이블 `not_when` 필드 끝에 아래 문구를 추가한다.

```
과거 회상 서술(~했었습니다, ~했었는데, 예전에~) 시 제외
```

**스크립트로 일괄 처리:**
```python
# scripts/add_past_tense_exclusion.py
import json

path = "data/micro_labels/positive_micro_labels.json"
with open(path, encoding="utf-8") as f:
    data = json.load(f)

suffix = ", 과거 회상 서술(~했었습니다, ~했었는데, 예전에~) 시 제외"
for label in data["micro_labels"]:
    if suffix not in label.get("not_when", ""):
        label["not_when"] = label.get("not_when", "") + suffix

with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("완료")
```

---

### M2. [MEDIUM] 단문 definition 확장

#### M17-01 — 상황적 유연성

**before:** `"definition": "변화에 빠르게 적응"`

**after:**
```json
"definition": "예상치 못한 상황 변화나 새로운 요구사항에 방어적 저항 없이 빠르게 적응하는 능력. 계획을 유연하게 수정하고 다양한 접근 방식을 기꺼이 시도하는 행동으로 나타남"
```

#### M24-01 — 운영 안정성 유지

**before:** `"definition": "안정적인 운영 환경과 프로세스 유지"`

**after:**
```json
"definition": "업무 프로세스, 시스템, 팀 루틴을 일관되게 유지함으로써 예측 가능하고 안정적인 운영 환경을 만드는 행동. 변화 중에도 핵심 운영 리듬을 흔들리지 않게 지키는 것을 포함"
```

#### M30-01 — 언행 일치

**before:** `"definition": "말한 것과 실제 행동이 일치하고 일관성 유지"`

**after:**
```json
"definition": "공개적으로 약속한 내용, 선언한 가치, 제시한 방향을 실제 행동과 결정에서 일관되게 구현하는 것. 사소한 약속도 반드시 이행하고, 지키지 못할 경우 즉시 설명하는 행동 패턴"
```

---

### M3. [MEDIUM] 경계 불명확 레이블 쌍 not_when 보강

#### M19-01(빠른 결정) vs N19-01(일방적 결정)

**M19-01 not_when 추가:**
```json
"not_when": "충분한 정보 없이 단독 결정, 관련자 의견 완전 배제, 숙려 기간 필요한 중대 사안의 즉흥 결정, 과거 회상 서술"
```

**N19-01 when 보강:**
```json
"when": "의견수렴 절차를 생략하고 본인 판단만으로 결정, 반대 의견 있음에도 일방적으로 추진, 팀 동의 없이 방향 전환",
"not_when": "위기 상황에서 신속한 결정(의견수렴 후), 합의된 의사결정 프레임 내 결정, 과거 회상 서술"
```

#### M05-02(변화 실행) vs N05-02(준비 없는 변화)

**M05-02 not_when 추가:**
```json
"not_when": "리스크 평가 없이 즉시 실행, 관련자 안내 없는 변경, 인프라·자원 미확보 상태에서 강행, 과거 회상 서술"
```

**N05-02 when 보강:**
```json
"when": "변화 필요성은 있으나 실행 준비(인력/시스템/예산/교육)가 갖춰지지 않은 상태에서 강행, 구성원에게 변화를 통보만 하고 지원 없이 진행"
```

---

## Part 2. 벡터 DB 청크 구조 개선

---

### V1. [핵심] 레이블당 다중 벡터 생성

**현재 문제:** 레이블 1개 = 벡터 1개. 정의/상황/제외 조건이 하나의 임베딩으로 압축되어 의미 손실.

**개선:** 레이블 1개 = 벡터 3개 (정의 벡터 + 상황 벡터 + 통합 벡터)

#### build_vector_db.py 수정

`load_labels()` 함수를 아래로 교체한다.

```python
def build_label_vectors(item):
    """레이블 1개에서 다중 벡터 텍스트 생성"""
    lid = item['label_id']
    name = item.get('label_name', '')
    definition = item.get('definition', '')
    when = item.get('when', '')
    not_when = item.get('not_when', '')

    vectors = []

    # 벡터 1: 정의 벡터 — 레이블의 핵심 의미
    if definition:
        vectors.append({
            'label_id': lid,
            'vector_type': 'definition',
            'text': f"{lid}: {name}. {definition}"
        })

    # 벡터 2: 상황 벡터 — 발동 조건 + 제외 조건
    if when or not_when:
        situation_text = f"{lid}: {name}"
        if when:
            situation_text += f" | 상황: {when}"
        if not_when:
            situation_text += f" | 제외: {not_when}"
        vectors.append({
            'label_id': lid,
            'vector_type': 'situation',
            'text': situation_text
        })

    # 벡터 3: 통합 벡터 — 정의 + 발동 조건 (검색 앵커)
    full_text = f"{lid}: {name}"
    if definition:
        full_text += f". {definition}"
    if when:
        full_text += f". 적용 상황: {when}"
    vectors.append({
        'label_id': lid,
        'vector_type': 'full',
        'text': full_text
    })

    return vectors


def load_labels():
    """긍정/부정 라벨 로드 — 다중 벡터 방식"""
    all_vectors = []     # {'label_id', 'vector_type', 'text'}
    label_texts = []
    label_ids = []
    vector_types = []    # 메타데이터: 어떤 종류의 벡터인지

    for path_key, json_path in [
        ('positive', DATASET_DIR / "positive_micro_labels_enhanced.json"),
        ('negative', DATASET_DIR / "negative_micro_labels_enhanced.json"),
    ]:
        if not json_path.exists():
            print(f"  경고: {json_path} 없음, 건너뜀")
            continue
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for item in data.get('micro_labels', []):
            for vec in build_label_vectors(item):
                all_vectors.append(vec)
                label_texts.append(vec['text'])
                label_ids.append(vec['label_id'])
                vector_types.append(vec['vector_type'])

    print(f"총 {len(all_vectors)}개 벡터 생성 ({len(set(label_ids))}개 레이블)")
    return all_vectors, label_texts, label_ids, vector_types
```

메타데이터 저장 부분도 `vector_types`를 포함하도록 수정한다.

```python
metadata = {
    'label_ids': label_ids,
    'label_texts': label_texts,
    'vector_types': vector_types,       # 추가
    'dimension': dimension,
    'model_name': 'nlpai-lab/KoE5',
    'total_labels': len(set(label_ids)),
    'total_vectors': len(label_ids),    # 추가
    'version': 'v3.0'
}
```

---

### V1-B. vector_search.py — 다중 벡터 검색 결과 병합

`search()` 메서드를 수정하여, 같은 `label_id`에서 온 여러 벡터 중 최고 신뢰도만 남긴다.

```python
def search(self, text: str, k=15, expand=True) -> list:
    """벡터 검색 수행 — 다중 벡터 병합"""
    query = self.expand_query(text) if expand else text
    vec = self.model.encode([query]).astype('float32')

    # 다중 벡터가 있으므로 더 많이 가져온 뒤 병합
    fetch_k = k * 3
    distances, indices = self.index.search(vec, fetch_k)

    # label_id별 최고 신뢰도만 유지
    best: dict[str, dict] = {}
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0:
            continue
        label_id = self.label_ids[idx]
        confidence = max(0.0, 1.0 - (dist / 2.0))
        vector_type = self.vector_types[idx] if hasattr(self, 'vector_types') else 'full'

        if label_id not in best or confidence > best[label_id]['confidence']:
            best[label_id] = {
                'label_id': label_id,
                'confidence': float(round(confidence, 4)),
                'distance': float(round(float(dist), 4)),
                'vector_type': vector_type,
                'text': self.label_texts[idx]
            }

    # 신뢰도 내림차순 정렬 후 상위 k개 반환
    results = sorted(best.values(), key=lambda x: x['confidence'], reverse=True)
    return results[:k]
```

`__init__`에서 `vector_types` 로드 추가:
```python
self.vector_types = self.metadata.get('vector_types', ['full'] * len(self.label_ids))
```

---

### V2. [핵심] 학습 샘플 보조 인덱스 추가

**현재 문제:** `dataset/ori/batch*.json`의 12,460개 실제 한국어 문장이 검색에 반영되지 않음.

#### build_vector_db.py — 샘플 인덱스 빌더 추가

```python
def load_training_samples(max_per_label=20):
    """학습 샘플 로드 — clean 샘플 위주로 최대 max_per_label개"""
    samples = []
    sample_texts = []
    sample_label_ids = []

    batch_files = sorted(DATASET_DIR.glob("batch*.json"))
    print(f"  배치 파일 {len(batch_files)}개 발견")

    label_count: dict[str, int] = {}

    for batch_file in batch_files:
        with open(batch_file, 'r', encoding='utf-8') as f:
            batch = json.load(f)
        for item in batch:
            lid = item.get('label_id', '')
            data_type = item.get('data_type', 'clean')
            text = item.get('text', '').strip()

            if not text or not lid:
                continue
            # clean 샘플 우선, hard_negative는 절반 비율
            if data_type == 'hard_negative' and label_count.get(lid, 0) >= max_per_label // 2:
                continue
            if label_count.get(lid, 0) >= max_per_label:
                continue

            label_count[lid] = label_count.get(lid, 0) + 1
            samples.append({'label_id': lid, 'text': text, 'data_type': data_type})
            sample_texts.append(text)
            sample_label_ids.append(lid)

    print(f"  총 {len(samples)}개 샘플 로드 ({len(set(sample_label_ids))}개 레이블)")
    return samples, sample_texts, sample_label_ids


def build_sample_index(model, sample_texts, dimension):
    """학습 샘플 보조 인덱스 구축"""
    print("  샘플 벡터화 중...")
    embeddings = model.encode(sample_texts, show_progress_bar=True, batch_size=64)
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings.astype('float32'))
    return index
```

`main()` 함수에 아래 단계 추가 (기존 [5/5] 저장 단계 이전):

```python
# 5. 학습 샘플 보조 인덱스
print("\n[5/6] 학습 샘플 보조 인덱스 구축 중...")
samples, sample_texts, sample_label_ids = load_training_samples(max_per_label=20)
if samples:
    sample_index = build_sample_index(model, sample_texts, dimension)
    faiss.write_index(sample_index, str(VECTOR_DIR / "sample_vectors.faiss"))
    sample_metadata = {
        'label_ids': sample_label_ids,
        'label_texts': sample_texts,
        'total_samples': len(samples),
        'version': 'v3.0'
    }
    with open(VECTOR_DIR / "sample_metadata.json", 'w', encoding='utf-8') as f:
        json.dump(sample_metadata, f, ensure_ascii=False, indent=2)
    print(f"  샘플 인덱스 저장 완료 ({len(samples)}개)")
```

---

### V2-B. vector_search.py — 보조 인덱스 통합 검색

`VectorSearcher.__init__`에 샘플 인덱스 로드 추가:

```python
# 샘플 보조 인덱스 (있으면 로드)
sample_index_path = VECTOR_DIR / "sample_vectors.faiss"
sample_meta_path = VECTOR_DIR / "sample_metadata.json"
if sample_index_path.exists() and sample_meta_path.exists():
    self.sample_index = faiss.read_index(str(sample_index_path))
    with open(sample_meta_path, 'r', encoding='utf-8') as f:
        sample_meta = json.load(f)
    self.sample_label_ids = sample_meta['label_ids']
    self.sample_label_texts = sample_meta['label_texts']
    print(f"샘플 인덱스 로드: {self.sample_index.ntotal}개")
else:
    self.sample_index = None
    self.sample_label_ids = []
    self.sample_label_texts = []
```

`search()` 메서드에 보조 인덱스 병합 로직 추가:

```python
def _search_sample_index(self, vec: np.ndarray, k: int) -> dict:
    """샘플 인덱스 검색 — label_id별 최고 신뢰도 반환"""
    if self.sample_index is None:
        return {}

    distances, indices = self.sample_index.search(vec, k * 2)
    best: dict[str, float] = {}
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0:
            continue
        lid = self.sample_label_ids[idx]
        confidence = max(0.0, 1.0 - (dist / 2.0))
        if lid not in best or confidence > best[lid]:
            best[lid] = confidence
    return best


def search(self, text: str, k=15, expand=True) -> list:
    query = self.expand_query(text) if expand else text
    vec = self.model.encode([query]).astype('float32')

    # --- 레이블 정의 인덱스 검색 ---
    fetch_k = k * 3
    distances, indices = self.index.search(vec, fetch_k)
    best: dict[str, dict] = {}
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0:
            continue
        lid = self.label_ids[idx]
        confidence = max(0.0, 1.0 - (dist / 2.0))
        vector_type = self.vector_types[idx] if hasattr(self, 'vector_types') else 'full'
        if lid not in best or confidence > best[lid]['confidence']:
            best[lid] = {
                'label_id': lid,
                'confidence': float(round(confidence, 4)),
                'distance': float(round(float(dist), 4)),
                'vector_type': vector_type,
                'text': self.label_texts[idx],
                'source': 'label'
            }

    # --- 샘플 보조 인덱스 병합 ---
    sample_best = self._search_sample_index(vec, k)
    for lid, sample_conf in sample_best.items():
        sample_conf = float(round(sample_conf, 4))
        if lid not in best:
            best[lid] = {
                'label_id': lid,
                'confidence': sample_conf,
                'distance': 0.0,
                'vector_type': 'sample',
                'text': '',
                'source': 'sample'
            }
        elif sample_conf > best[lid]['confidence']:
            # 샘플이 더 높으면 신뢰도만 업데이트 (source는 sample로 표시)
            best[lid]['confidence'] = sample_conf
            best[lid]['source'] = 'sample'

    results = sorted(best.values(), key=lambda x: x['confidence'], reverse=True)
    return results[:k]
```

---

### V4. [중간] 신뢰도 기반 조건부 쿼리 확장

**현재 문제:** `expand_query()`가 패턴 감지 시 항상 키워드를 추가함. 이미 고신뢰도 쿼리에 확장을 적용하면 임베딩이 의도에서 멀어짐.

`search_with_threshold()` 메서드에서 확장 전 사전 검색을 수행한다.

```python
def search_with_threshold(self, text: str, k=15) -> dict:
    """임계값 기반 하이브리드 검색 — 조건부 쿼리 확장"""

    # 1단계: 확장 없이 기본 신뢰도 측정
    raw_results = self.search(text, k=5, expand=False)
    base_confidence = raw_results[0]['confidence'] if raw_results else 0.0

    # 2단계: 신뢰도가 낮을 때만 확장 적용
    use_expand = base_confidence < 0.65
    results = self.search(text, k=k, expand=use_expand)

    # 역접 형태소 확인
    adversative_type = self.check_adversative_particles(text)
    should_call, reason = self.should_call_llm(results)

    if adversative_type != "none" and not should_call:
        should_call = True
        reason = f"{adversative_type} 포함으로 LLM 호출"

    top_confidence = results[0]['confidence'] if results else 0.0
    return {
        'results': results,
        'should_call_llm': should_call,
        'reason': reason,
        'top_confidence': top_confidence,
        'query_expanded': use_expand   # 디버그 정보
    }
```

---

### V6. [낮음] 부정어 심각도 분류 — LLM 과잉 호출 방지

**현재 문제:** "하지만", "그러나" 등장만으로 LLM을 무조건 호출. 양보절과 실제 부정을 구분하지 못함.

`check_adversative_particles()` 메서드를 아래로 교체한다.

```python
# vector_search_patterns.json에 추가할 패턴 (또는 코드 내 상수로 정의)
CRITICAL_ADVERSATIVE = [
    '지키지 않', '못했', '거짓', '실제로는', '사실은',
    '속였', '취소됐', '없었', '이행하지', '안 됐'
]
SOFT_ADVERSATIVE = ['하지만', '그러나', '그런데', '그렇지만', '반면']

def check_adversative_particles(self, text: str) -> str:
    """
    역접 형태소 심각도 분류
    - critical: 약속 불이행, 사실과 다른 발언 → LLM 의무 호출
    - soft: 단순 양보·대조 → 벡터 신뢰도 기반 판단
    - none: 해당 없음
    """
    if any(p in text for p in CRITICAL_ADVERSATIVE):
        return "explicit_adversative"   # 기존 코드와 호환 유지

    # soft는 벡터 신뢰도가 낮을 때만 LLM 호출하도록 caller에서 처리
    if any(p in text for p in SOFT_ADVERSATIVE):
        return "soft_adversative"

    return "none"
```

`search_with_threshold()`에서 `soft_adversative` 분기 처리:

```python
if adversative_type == "explicit_adversative" and not should_call:
    should_call = True
    reason = "명시적 역접 포함 — LLM 의무 호출"
elif adversative_type == "soft_adversative" and top_confidence < 0.65:
    should_call = True
    reason = f"양보절 + 중간 신뢰도({top_confidence:.2f}) — LLM 호출"
```

---

## Part 3. 검증 절차

### Step 1. 데이터 정합성 검증

```python
# scripts/validate_data.py
import json, glob, sys

errors = []

# C2: context_rules.json 중복 키 체크
import re
text = open("data/engine/context_rules.json", encoding="utf-8").read()
keys = re.findall(r'"(T\d+)":', text)
dups = {k for k in keys if keys.count(k) > 1}
if dups:
    errors.append(f"[C2] context_rules.json 중복 키: {dups}")

# C1: definition 필드 누락 체크
with open("data/micro_labels/positive_micro_labels.json", encoding="utf-8") as f:
    pos = json.load(f)
for label in pos["micro_labels"]:
    if not label.get("definition"):
        errors.append(f"[C1] definition 누락: {label['label_id']}")

# C3: negative_mapping_rules.json T10, T11 포함 여부
with open("data/engine/negative_mapping_rules.json", encoding="utf-8") as f:
    nmr = json.load(f)
mapped_ids = {r["trait_id"] for r in nmr.get("trait_negative_rules", [])}
for tid in ["T10", "T11"]:
    if tid not in mapped_ids:
        errors.append(f"[C3] {tid} 매핑 없음")

if errors:
    print("❌ 검증 실패:")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)
else:
    print("✅ 데이터 정합성 검증 통과")
```

### Step 2. 벡터 DB 재빌드

```bash
python build_vector_db.py
```

예상 출력:
```
총 534개 벡터 생성 (178개 레이블)   ← 기존 178개에서 3배
총 3560개 샘플 로드 (178개 레이블)   ← 샘플 인덱스
```

### Step 3. 파이프라인 통합 테스트

앱 실행 후 아래 5개 케이스를 수동 입력하여 결과 확인:

| 케이스 | 입력 | 기대 결과 |
|--------|------|----------|
| T04 위기 결단 | "문제가 발생하여 즉시 결단을 내렸다" | M19-01 (고신뢰도) |
| T105 약속 불이행 | "약속했지만 실제로는 지키지 않았다" | N30-01, N02-01 |
| T103 데이터 조작 | "데이터를 의도적으로 수정했다" | N34-01 |
| M19/N19 경계 (긍정) | "의견을 충분히 들은 후 신속하게 결정했다" | M19-01 |
| M19/N19 경계 (부정) | "혼자서 바로 결정해버렸다. 팀 의견은 듣지 않았다" | N19-01 |

### Step 4. 성능 비교

```python
# scripts/benchmark.py
# 개선 전/후 recall@5 비교 스크립트
test_cases = [
    ("문제가 발생하여 즉시 결단을 내렸다", "M19-01"),
    ("팀원들의 의견을 경청하고 반영했다", "M15-02"),
    ("성과에 대한 공로를 혼자 가져갔다", "N09-01"),
]
# 각 케이스에서 상위 5개 결과에 기대 레이블 포함 여부 측정
```

---

## 수정 파일 목록 요약

| 우선순위 | 파일 | 수정 내용 |
|---------|------|---------|
| CRITICAL | `data/micro_labels/positive_micro_labels.json` | M14-01, M14-02, M15-06 definition 추가 |
| CRITICAL | `data/engine/context_rules.json` | T14 중복 키 제거 |
| CRITICAL | `data/engine/negative_mapping_rules.json` | T10, T11 매핑 추가 |
| HIGH | `data/micro_labels/positive_micro_labels.json` | H4~H6 중복 레이블 경계 재정의 |
| HIGH | `data/micro_labels/positive_micro_labels.json` | M1 과거시제 제외 문구 추가 (스크립트) |
| MEDIUM | `data/micro_labels/positive_micro_labels.json` | M2 단문 definition 3개 확장 |
| MEDIUM | `data/micro_labels/positive/negative_micro_labels.json` | M3 경계 불명확 not_when 보강 |
| 벡터DB | `build_vector_db.py` | V1 다중 벡터 + V2 샘플 인덱스 |
| 벡터DB | `src/vector_search.py` | 다중 벡터 병합 + 샘플 통합 + V4 조건부 확장 + V6 부정어 분류 |
