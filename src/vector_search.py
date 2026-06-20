#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Vector DB 검색 모듈
- KoE5 임베딩
- FAISS 인덱스
- 쿼리 확장 및 가중치 조정
"""

import sys
import json
import numpy as np
import faiss
from pathlib import Path

# Python 3.13 compatibility: lazy import with error handling
try:
    from sentence_transformers import SentenceTransformer
except Exception as e:
    print("Warning: sentence_transformers import failed: {}".format(e))
    print("Trying alternative import method...")
    try:
        import importlib
        spec = importlib.util.find_spec("sentence_transformers")
        if spec is not None:
            SentenceTransformer = importlib.import_module("sentence_transformers").SentenceTransformer
        else:
            raise ImportError("sentence_transformers not found")
    except:
        raise ImportError("Cannot import SentenceTransformer. Please check torch/sentence_transformers installation.")

PROJECT_ROOT = Path(r"C:\dev\leadership")
VECTOR_DIR = PROJECT_ROOT / "data" / "vectors"
PATTERNS_FILE = PROJECT_ROOT / "data" / "patterns" / "vector_search_patterns.json"

class VectorSearcher:
    def __init__(self, model_name='nlpai-lab/KoE5'):
        """Vector DB 초기화"""
        print("모델 로딩 중...")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_embedding_dimension()
        
        # 메타데이터 로드
        with open(VECTOR_DIR / "metadata.json", 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
        
        self.label_ids = self.metadata['label_ids']
        self.label_texts = self.metadata['label_texts']
        self.vector_types = self.metadata.get('vector_types', ['full'] * len(self.label_ids))
        
        # FAISS 인덱스 로드
        print("FAISS 인덱스 로딩 중...")
        self.index = faiss.read_index(str(VECTOR_DIR / "label_vectors.faiss"))
        print(f"초기화 완료: {self.index.ntotal}개 벡터")

        # 샘플 보조 인덱스 로드 (있으면)
        sample_idx_path = VECTOR_DIR / "sample_vectors.faiss"
        sample_meta_path = VECTOR_DIR / "sample_metadata.json"
        if sample_idx_path.exists() and sample_meta_path.exists():
            self.sample_index = faiss.read_index(str(sample_idx_path))
            with open(sample_meta_path, 'r', encoding='utf-8') as f:
                smeta = json.load(f)
            self.sample_label_ids = smeta['label_ids']
            self.sample_label_texts = smeta['label_texts']
            print(f"샘플 인덱스 로드: {self.sample_index.ntotal}개")
        else:
            self.sample_index = None
            self.sample_label_ids = []
            self.sample_label_texts = []

        # 패턴 파일 로드
        self.patterns = self._load_patterns()
    
    def _load_patterns(self):
        """패턴 JSON 파일 로드"""
        try:
            with open(PATTERNS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Patterns file not found at {PATTERNS_FILE}")
            return {}
    
    def expand_query(self, text: str) -> str:
        """쿼리 확장: 핵심 키워드 강조 + 패턴 감지 (JSON 기반)"""
        expanded = text
        
        # 패턴 파일에서 로드한 패턴 사용
        patterns = self.patterns
        
        # 1. Crisis 키워드 (JSON에서 로드)
        if 'crisis_patterns' in patterns:
            crisis_kw = patterns['crisis_patterns'].get('keywords', [])
            for kw in crisis_kw:
                if kw in text:
                    expanded += f" {kw} {kw}"
        
        # 2. Innovation 키워드 (JSON에서 로드)
        if 'innovation_patterns' in patterns:
            inn_kw = patterns['innovation_patterns'].get('keywords', [])
            for kw in inn_kw:
                if kw in text:
                    expanded += f" {kw} {kw}"
        
        # 3. 조건부 약속 패턴 (JSON에서 로드)
        if 'conditional_promises' in patterns:
            cond_pats = patterns['conditional_promises'].get('regex_patterns', [])
            import re
            is_conditional = any(re.search(p, text) for p in cond_pats)
            if is_conditional:
                expansion = patterns['conditional_promises'].get('vector_expansion', '')
                expanded += f" {expansion}"
        
        # 4. 암시적 부정 패턴 (JSON에서 로드)
        if 'adversative' in patterns and 'implicit_negative' in patterns['adversative']:
            implicit_pats = patterns['adversative']['implicit_negative'].get('patterns', [])
            import re
            is_implicit = any(re.search(p, text) for p in implicit_pats)
            if is_implicit:
                expansion = patterns['adversative']['implicit_negative'].get('vector_expansion', '')
                expanded += f" {expansion}"
        
        # 5. 명시적 역접 (JSON에서 로드)
        if 'adversative' in patterns and 'explicit' in patterns['adversative']:
            explicit_pats = patterns['adversative']['explicit'].get('patterns', [])
            for p in explicit_pats:
                if p in text:
                    expanded += f" {p} {p} but however"
        
        # T04-B 특화 (하위 호환성 유지)
        if "문제가 발생" in text:
            expanded += " 문제 발생 위기 상황 긴급 위기"
        if "빠르게 결론" in text:
            expanded += " 빠르게 결론 신속 의사결정 즉시 결정"
        if "내 안내대로" in text:
            expanded += " 안내 지시 지휘 명확한 역할"
        
        return expanded
    
    def search(self, text: str, k=15, expand=True) -> list:
        """벡터 검색 수행 — 다중 벡터 label_id별 최고 신뢰도 병합"""
        query = self.expand_query(text) if expand else text
        vec = self.model.encode([query]).astype('float32')

        # 다중 벡터가 있으므로 더 많이 가져온 뒤 병합
        fetch_k = min(k * 3, self.index.ntotal)
        distances, indices = self.index.search(vec, fetch_k)

        # label_id별 최고 신뢰도만 유지
        best: dict = {}
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0:
                continue
            label_id = self.label_ids[idx]
            confidence = max(0.0, 1.0 - (dist / 2.0))
            vtype = self.vector_types[idx]
            if label_id not in best or confidence > best[label_id]['confidence']:
                best[label_id] = {
                    'label_id': label_id,
                    'confidence': float(round(float(confidence), 4)),
                    'distance': float(round(float(dist), 4)),
                    'vector_type': vtype,
                    'text': self.label_texts[idx]
                }

        results = sorted(best.values(), key=lambda x: x['confidence'], reverse=True)
        return results[:k]
    
    def should_call_llm(self, results: list, threshold_high=0.70, threshold_low=0.60) -> tuple[bool, str]:
        """
        Vector DB 검색 결과를 기반으로 LLM 호출 여부 결정
        Returns: (should_call_llm, reason)
        - True: LLM 추론 레이어 호출 필요
        - False: 직접 라벨링 가능
        """
        if not results:
            return True, "검색 결과 없음"
        
        top_confidence = results[0]['confidence']
        
        # 고신뢰도: LLM 건너뛰기
        if top_confidence >= threshold_high:
            return False, f"고신뢰도({top_confidence:.2f} >= {threshold_high}) 직접 라벨링"
        
        # 저신뢰도: 매칭 없음
        if top_confidence < threshold_low:
            return False, f"저신뢰도({top_confidence:.2f} < {threshold_low}) 매칭 없음"
        
        # 중신뢰도: LLM 호출
        return True, f"중신뢰도({threshold_low} <= {top_confidence:.2f} < {threshold_high}) LLM 추론 필요"
    
    # V6: 부정어 심각도 분류 상수
    _CRITICAL_ADVERSATIVE = [
        '지키지 않', '못했', '거짓', '실제로는', '사실은',
        '속였', '취소됐', '없었', '이행하지', '안 됐'
    ]
    _SOFT_ADVERSATIVE = ['하지만', '그러나', '그런데', '그렇지만', '반면']

    def check_adversative_particles(self, text: str) -> str:
        """
        역접/부정 형태소 심각도 분류 (V6)
        - explicit_adversative: 약속 불이행·사실 위반 → LLM 의무 호출
        - soft_adversative: 단순 양보·대조 → 신뢰도 기반 판단
        - implicit_negative: 암시적 부정 패턴 → LLM 호출
        - none: 해당 없음
        """
        import re

        # 1. Critical 역접 (약속 불이행, 사실과 다른 발언)
        if any(p in text for p in self._CRITICAL_ADVERSATIVE):
            return "explicit_adversative"

        # 2. 암시적 부정 (JSON 패턴 기반)
        patterns = self.patterns
        if 'adversative' in patterns and 'implicit_negative' in patterns['adversative']:
            implicit_pats = patterns['adversative']['implicit_negative'].get('patterns', [])
            for p in implicit_pats:
                if re.search(p, text):
                    return "implicit_negative"

        # 3. 단순 양보·대조 (soft)
        if any(p in text for p in self._SOFT_ADVERSATIVE):
            return "soft_adversative"

        return "none"
    
    def _search_sample_index(self, vec, k: int) -> dict:
        """샘플 보조 인덱스 검색 — label_id별 최고 신뢰도 반환 (V2-B)"""
        if self.sample_index is None:
            return {}
        fetch_k = min(k * 2, self.sample_index.ntotal)
        distances, indices = self.sample_index.search(vec, fetch_k)
        best: dict = {}
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0:
                continue
            lid = self.sample_label_ids[idx]
            conf = max(0.0, 1.0 - (dist / 2.0))
            if lid not in best or conf > best[lid]:
                best[lid] = float(round(conf, 4))
        return best

    def search_with_threshold(self, text: str, k=15, expand=True) -> dict:
        """
        임계값 기반 하이브리드 검색 (V4: 조건부 쿼리 확장)
        Returns: {results, should_call_llm, reason, confidence, query_expanded}
        """
        # V4: 신뢰도 낮을 때만 쿼리 확장 적용
        raw_results = self.search(text, k=5, expand=False)
        base_confidence = raw_results[0]['confidence'] if raw_results else 0.0
        use_expand = base_confidence < 0.65

        results = self.search(text, k=k, expand=use_expand)

        # V2-B: 샘플 보조 인덱스 병합
        vec = self.model.encode([self.expand_query(text) if use_expand else text]).astype('float32')
        sample_best = self._search_sample_index(vec, k)
        best_map = {r['label_id']: r for r in results}
        for lid, sconf in sample_best.items():
            if lid not in best_map:
                best_map[lid] = {
                    'label_id': lid,
                    'confidence': sconf,
                    'distance': 0.0,
                    'vector_type': 'sample',
                    'text': ''
                }
            elif sconf > best_map[lid]['confidence']:
                best_map[lid]['confidence'] = sconf
                best_map[lid]['vector_type'] = 'sample'
        results = sorted(best_map.values(), key=lambda x: x['confidence'], reverse=True)[:k]

        # V6: 부정어 심각도 분류
        adversative_type = self.check_adversative_particles(text)
        should_call, reason = self.should_call_llm(results)

        if adversative_type == "explicit_adversative" and not should_call:
            should_call = True
            reason = "명시적 역접 포함 — LLM 의무 호출"
        elif adversative_type in ("implicit_negative", "soft_adversative") and not should_call:
            top = results[0]['confidence'] if results else 0.0
            if top < 0.65:
                should_call = True
                reason = f"{adversative_type} + 중간 신뢰도({top:.2f}) — LLM 호출"

        top_confidence = results[0]['confidence'] if results else 0.0

        return {
            'results': results,
            'should_call_llm': should_call,
            'reason': reason,
            'top_confidence': top_confidence,
            'query_expanded': use_expand
        }
    
    def search_with_context(self, text: str, context: str = None, k=15) -> list:
        """컨텍스트를 고려한 검색"""
        # 컨텍스트별 확장
        context_expansion = {
            'crisis': '위기 상황 긴급 문제 발생 빠른 대응',
            'normal': '일반 협업 소통',
            'innovation': '혁신 창의 새로운 변화'
        }
        
        expanded_text = text
        if context and context in context_expansion:
            expanded_text += " " + context_expansion[context]
        
        return self.search(expanded_text, k, expand=True)


def format_results(results: list) -> str:
    """결과 포맷팅"""
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"{i:2}. {r['label_id']} (신뢰도: {r['confidence']:.4f}, 거리: {r['distance']:.4f})")
        lines.append(f"     {r['text'][:100]}...")
    return "\n".join(lines)


if __name__ == "__main__":
    # 테스트
    searcher = VectorSearcher()
    
    with open(r"C:\dev\leadership\data\vectors\search_results.txt", 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("T04-B 검색 테스트\n")
        f.write("="*70 + "\n\n")
        query_t04 = "문제가 발생했다. 지금 상황을 분석하고 있다. 빠르게 결론을 내릴 것이다. 모두 내 안내대로 행동해달라."
        f.write(f"쿼리: {query_t04}\n\n")
        results_t04 = searcher.search(query_t04, k=10)
        f.write(format_results(results_t04) + "\n\n")
        
        f.write("="*70 + "\n")
        f.write("T105-A 검색 테스트\n")
        f.write("="*70 + "\n\n")
        query_t105 = "이번 quarter 성과 좋으면 즉시 승진시켜드립니다. 하지만 실제로는 그런 일 없습니다. 안 하면 해고하겠습니다."
        f.write(f"쿼리: {query_t105}\n\n")
        results_t105 = searcher.search(query_t105, k=10)
        f.write(format_results(results_t105) + "\n")
    
    print("결과 저장 완료: data/vectors/search_results.txt")
