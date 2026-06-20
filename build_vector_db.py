#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 1: Vector DB 구축 (v2.1)
- KoE5 모델 로드
- 라벨 데이터 벡터화 (enhanced JSON 기반)
- FAISS 인덱스 생성
"""

import sys
import json
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer

# 프로젝트 경로
PROJECT_ROOT = Path(r"C:\dev\leadership")
DATA_DIR = PROJECT_ROOT / "data"
DATASET_DIR = PROJECT_ROOT / "dataset" / "ori"
VECTOR_DIR = DATA_DIR / "vectors"

def build_label_vectors(item):
    """레이블 1개에서 다중 벡터 텍스트 생성 (정의/상황/통합 3벡터)"""
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
        sit = f"{lid}: {name}"
        if when:
            sit += f" | 상황: {when}"
        if not_when:
            sit += f" | 제외: {not_when}"
        vectors.append({
            'label_id': lid,
            'vector_type': 'situation',
            'text': sit
        })

    # 벡터 3: 통합 벡터 — 정의 + 발동 조건 (검색 앵커)
    full = f"{lid}: {name}"
    if definition:
        full += f". {definition}"
    if when:
        full += f". 적용 상황: {when}"
    vectors.append({
        'label_id': lid,
        'vector_type': 'full',
        'text': full
    })

    return vectors


def load_labels():
    """긍정/부정 라벨 로드 — 레이블당 다중 벡터 방식"""
    all_vectors = []
    label_texts = []
    label_ids = []
    vector_types = []

    sources = [
        DATASET_DIR / "positive_micro_labels_enhanced.json",
        DATASET_DIR / "negative_micro_labels_enhanced.json",
    ]

    for path in sources:
        if not path.exists():
            print(f"  경고: {path.name} 없음, 건너뜀")
            continue
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for item in data.get('micro_labels', []):
            for vec in build_label_vectors(item):
                all_vectors.append(vec)
                label_texts.append(vec['text'])
                label_ids.append(vec['label_id'])
                vector_types.append(vec['vector_type'])

    unique_labels = len(set(label_ids))
    print(f"총 {len(all_vectors)}개 벡터 생성 ({unique_labels}개 레이블 × 최대 3벡터)")
    return all_vectors, label_texts, label_ids, vector_types


def load_training_samples(max_per_label=20):
    """학습 샘플 로드 — clean 위주, 레이블당 최대 max_per_label개"""
    samples = []
    sample_texts = []
    sample_label_ids = []
    label_count: dict = {}

    batch_files = sorted(DATASET_DIR.glob("batch*.json"))
    print(f"  배치 파일 {len(batch_files)}개 발견")

    for batch_file in batch_files:
        with open(batch_file, 'r', encoding='utf-8') as f:
            batch = json.load(f)
        for item in batch:
            lid = item.get('label_id', '')
            data_type = item.get('data_type', 'clean')
            text = item.get('text', '').strip()
            if not text or not lid:
                continue
            cnt = label_count.get(lid, 0)
            # hard_negative는 절반 비율까지만
            if data_type == 'hard_negative' and cnt >= max_per_label // 2:
                continue
            if cnt >= max_per_label:
                continue
            label_count[lid] = cnt + 1
            samples.append({'label_id': lid, 'text': text, 'data_type': data_type})
            sample_texts.append(text)
            sample_label_ids.append(lid)

    print(f"  총 {len(samples)}개 샘플 로드 ({len(set(sample_label_ids))}개 레이블)")
    return samples, sample_texts, sample_label_ids


def build_faiss_index(embeddings, dimension):
    """FAISS 인덱스 생성"""
    # L2 거리 측정 (유클리드 거리)
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings.astype('float32'))
    return index


def test_search(model, index, label_ids, label_texts, query, k=10):
    """검색 테스트"""
    print(f"\n[검색 테스트]")
    print(f"쿼리: {query}")
    
    # 쿼리 벡터화
    query_vec = model.encode([query])
    distances, indices = index.search(query_vec.astype('float32'), k=k)
    
    print(f"\n상위 {k}개 결과:")
    results = []
    for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
        if idx < 0:
            continue
        lid = label_ids[idx]
        text = label_texts[idx]
        confidence = max(0, 1.0 - (dist / 2.0))  # 거리 → 신뢰도
        print(f"  {i+1}. {lid} (거리: {dist:.4f}, 신뢰도: {confidence:.4f})")
        print(f"     {text[:80]}...")
        results.append({'label_id': lid, 'confidence': confidence, 'text': text})
    
    return results


def main():
    print("=" * 70)
    print("Vector DB 구축 시작 (v2.1)")
    print("=" * 70)
    
    # 1. KoE5 모델 로드
    print("\n[1/5] KoE5 모델 로드 중...")
    try:
        model = SentenceTransformer('nlpai-lab/KoE5')
        dimension = model.get_sentence_embedding_dimension()
        print(f"  모델 로드 완료 (차원: {dimension})")
    except Exception as e:
        print(f"  오류: {e}")
        print("  대안 모델 (paraphrase-multilingual-MiniLM-L12-v2) 시도...")
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        dimension = model.get_sentence_embedding_dimension()
    
    # 2. 라벨 데이터 로드
    print("\n[2/5] 라벨 데이터 로드 중...")
    labels, label_texts, label_ids, vector_types = load_labels()
    
    # 3. 벡터화
    print("\n[3/5] 라벨 텍스트 벡터화 중...")
    embeddings = model.encode(label_texts, show_progress_bar=True)
    print(f"  벡터화 완료: {embeddings.shape}")
    
    # 4. FAISS 인덱스 구축
    print("\n[4/5] FAISS 인덱스 구축 중...")
    index = build_faiss_index(embeddings, dimension)
    print(f"  인덱스 구축 완료 (총 {index.ntotal}개 벡터)")
    
    # 5. 저장
    print("\n[5/5] 인덱스 및 메타데이터 저장 중...")
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)
    
    # FAISS 인덱스 저장
    faiss.write_index(index, str(VECTOR_DIR / "label_vectors.faiss"))
    
    # 메타데이터 저장
    metadata = {
        'label_ids': label_ids,
        'label_texts': label_texts,
        'vector_types': vector_types,
        'dimension': dimension,
        'model_name': 'nlpai-lab/KoE5',
        'total_labels': len(set(label_ids)),
        'total_vectors': len(label_ids),
        'version': 'v3.0'
    }
    with open(VECTOR_DIR / "metadata.json", 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"  저장 완료: {VECTOR_DIR}")

    # 5.5. 학습 샘플 보조 인덱스
    print("\n[5.5/6] 학습 샘플 보조 인덱스 구축 중...")
    samples, sample_texts, sample_label_ids = load_training_samples(max_per_label=20)
    if samples:
        print("  샘플 벡터화 중...")
        sample_embeddings = model.encode(sample_texts, show_progress_bar=True, batch_size=64)
        sample_index = build_faiss_index(sample_embeddings, dimension)
        faiss.write_index(sample_index, str(VECTOR_DIR / "sample_vectors.faiss"))
        sample_metadata = {
            'label_ids': sample_label_ids,
            'label_texts': sample_texts,
            'total_samples': len(samples),
            'version': 'v3.0'
        }
        with open(VECTOR_DIR / "sample_metadata.json", 'w', encoding='utf-8') as f:
            json.dump(sample_metadata, f, ensure_ascii=False, indent=2)
        print(f"  샘플 인덱스 저장 완료 ({len(samples)}개 → {VECTOR_DIR / 'sample_vectors.faiss'})")

    # 테스트 검색
    print("\n" + "=" * 70)
    print("테스트 검색")
    print("=" * 70)
    
    # T04-B 테스트
    t04_query = "문제가 발생했다. 지금 상황을 분석하고 있다. 빠르게 결론을 내릴 것이다."
    results_t04 = test_search(model, index, label_ids, label_texts, t04_query, k=10)
    
    # T105-A 테스트
    t105_query = "이번 quarter 성과 좋으면 즉시 승진시켜드립니다. 하지만 실제로는 그런 일 없습니다. 안 하면 해고하겠습니다."
    results_t105 = test_search(model, index, label_ids, label_texts, t105_query, k=10)
    
    # 결과 저장 (float32 -> float 변환)
    def convert_floats(obj):
        if isinstance(obj, dict):
            return {k: convert_floats(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_floats(v) for v in obj]
        elif hasattr(obj, 'item'):  # numpy float32 등
            return obj.item()
        return obj
    
    test_results = {
        'T04-B': {
            'query': t04_query,
            'results': results_t04
        },
        'T105-A': {
            'query': t105_query,
            'results': results_t105
        }
    }
    test_results = convert_floats(test_results)
    
    with open(VECTOR_DIR / "test_results.json", 'w', encoding='utf-8') as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 70)
    print("Vector DB 구축 완료!")
    print("=" * 70)
    print(f"인덱스: {VECTOR_DIR / 'label_vectors.faiss'}")
    print(f"메타데이타: {VECTOR_DIR / 'metadata.json'}")
    print(f"테스트 결과: {VECTOR_DIR / 'test_results.json'}")


if __name__ == "__main__":
    main()
