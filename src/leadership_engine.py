import math
import json
from collections import defaultdict
from pathlib import Path


class LeadershipEngine:
    def __init__(self, data_dir="./data"):
        self.data_dir = Path(data_dir)
        self._load_configs()

    def _load_configs(self):
        # 핵심 설정 파일 로드 (v4 우선, 없으면 v3 폴백 — append-only)
        trait_path = self.data_dir / 'traits/trait_definitions_v4.json'
        if not trait_path.exists():
            trait_path = self.data_dir / 'traits/trait_definitions.json'
        with open(trait_path, 'r', encoding='utf-8') as f:
            self.trait_definitions = json.load(f)['traits']
        
        self.trait_def_map = {t['trait_id']: t for t in self.trait_definitions}
        
        with open(self.data_dir / 'engine/hybrid_rules.json', 'r', encoding='utf-8') as f:
            hybrid_config = json.load(f)
            self.hybrid_rules = hybrid_config.get('hybrid_rules', [])
        
        # 추가 설정 파일 로드 (외부화된 설정 반영)
        config_files = {
            'scoring_config': self.data_dir / 'engine/scoring_config.json',
            'context_rules': self.data_dir / 'engine/context_rules.json',
            'auto_mapping_rules': self.data_dir / 'engine/auto_mapping_rules.json',
            'negative_mapping_rules': self.data_dir / 'engine/negative_mapping_rules.json'
        }
        
        for config_name, config_path in config_files.items():
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    setattr(self, config_name, json.load(f))
            else:
                print(f"Warning: {config_name} not found at {config_path}")
                setattr(self, config_name, {})
        
        self.positive_traits = [t for t in self.trait_definitions
                               if t.get('trait_type', 'positive') == 'positive']
        self.negative_traits = [t for t in self.trait_definitions
                               if t.get('trait_type', 'positive') == 'negative']
        
        self._calculate_k_traits()

    def _calculate_k_traits(self):
        for trait_def in self.trait_definitions:
            required = trait_def.get('required', [])
            optional = trait_def.get('optional', [])
            
            raw_max = len(required) * 1.0 + len(optional) * 1.0
            trait_def['calculated_k'] = math.log(1 + raw_max) if raw_max > 0 else 1.0

    def process(self, micro_labels, context: str = "normal"):
        """
        수정사항:
        - label_confidences: dict → defaultdict(list) 로 변경
          동일 label 여러 번 등장 시 confidence 리스트 누적
        - label_contexts: label별 등장 context set 누적
          → consistency 계산에 사용
        - label_count: label별 등장 횟수 누적
          → effective_count 기반 수확 체감 반영 가능
        - _calculate_confidence에 label_context_list 전달
        """
        # label별 confidence 리스트 누적
        label_conf_list = defaultdict(list)
        label_context_list = defaultdict(set)
        label_count = defaultdict(int)

        for ml in micro_labels:
            lid = ml['label_id']
            # confidence 타입 정규화 (str → float)
            conf_val = ml.get('confidence', 1.0)
            if isinstance(conf_val, str):
                try:
                    conf_val = float(conf_val)
                except (TypeError, ValueError):
                    conf_val = 1.0
            label_conf_list[lid].append(conf_val)
            label_context_list[lid].add(ml.get('context', 'normal'))
            label_count[lid] += 1

        # label_ids: 중복 포함 전체 목록 (Pattern Engine 매칭용)
        label_ids = [ml['label_id'] for ml in micro_labels]

        # label_confidences: label별 평균 confidence (Pattern Engine 입력용)
        label_confidences = {
            lid: round(sum(confs) / len(confs), 4)
            for lid, confs in label_conf_list.items()
        }

        positive_traits_results = []
        negative_traits_results = []
        
        for trait_def in self.positive_traits:
            strength, evidence = self._calculate_positive_trait(
                trait_def, label_ids, label_confidences, context
            )
            if strength > 0:
                positive_traits_results.append({
                    'trait_id': trait_def['trait_id'],
                    'name': trait_def['trait_name'],
                    'strength': strength,
                    'evidence': evidence
                })
        
        for trait_def in self.negative_traits:
            strength = self._calculate_negative_trait(
                trait_def, label_ids, label_confidences
            )
            if strength > 0:
                negative_traits_results.append({
                    'trait_id': trait_def['trait_id'],
                    'name': trait_def['trait_name'],
                    'strength': strength
                })
        
        positive_traits_results.sort(key=lambda x: x['strength'], reverse=True)
        negative_traits_results.sort(key=lambda x: x['strength'], reverse=True)
        
        # 통합 Trait 목록 생성 (긍정 + 부정)
        all_traits = []
        for pt in positive_traits_results:
            all_traits.append({
                'trait_id': pt['trait_id'],
                'name': pt['name'],
                'strength': pt['strength'],
                'type': 'positive',
                'evidence': pt.get('evidence', [])
            })
        for nt in negative_traits_results:
            all_traits.append({
                'trait_id': nt['trait_id'],
                'name': nt['name'],
                'strength': nt['strength'],
                'type': 'negative',
                'evidence': []
            })
        
        # 통합 strength 합계로 percentage 계산
        total_strength = sum(t['strength'] for t in all_traits) if all_traits else 1
        
        trait_percentages = []
        for t in all_traits:
            pct = round((t['strength'] / total_strength) * 100, 1) if total_strength > 0 else 0
            trait_percentages.append({
                'trait_id': t['trait_id'],
                'name': t['name'],
                'percentage': pct,
                'strength': t['strength'],
                'type': t['type']
            })
        
        trait_percentages = [t for t in trait_percentages if t['percentage'] >= 3.0]
        trait_percentages.sort(key=lambda x: x['percentage'], reverse=True)
        
        primary = trait_percentages[0] if trait_percentages else None
        secondary_list = trait_percentages[1:4] if len(trait_percentages) > 1 else []
        
        # 수정: label_context_list, label_count 전달
        confidence = self._calculate_confidence(
            micro_labels, label_confidences, label_context_list, label_count
        )
        
        risks = self._detect_risks(micro_labels, positive_traits_results, negative_traits_results)
        
        hybrid_traits = self._generate_hybrids(positive_traits_results)
        
        return {
            "primary": primary['trait_id'] if primary else None,
            "primary_name": primary['name'] if primary else None,
            "primary_strength": round(primary['strength'], 3) if primary else None,
            "primary_type": primary['type'] if primary else None,
            "secondary": [t['trait_id'] for t in secondary_list],
            "secondary_details": [(t['trait_id'], t['name'], t['percentage'], t['type']) for t in secondary_list],
            "confidence": confidence,
            "confidence_level": self._get_confidence_level(confidence),
            "evidence": primary.get('evidence', []) if primary else [],
            "trait_percentages": {t['trait_id']: t['percentage'] for t in trait_percentages},
            "trait_percentages_full": trait_percentages,
            "sorted_trait_list": [(t['trait_id'], t['percentage'], round(t['strength'], 3), t['type']) for t in trait_percentages],
            "negative_traits": [
                {'trait_id': t['trait_id'], 'name': t['name'], 'severity': round(t['strength'], 2)}
                for t in negative_traits_results[:5]
            ],
            "risks": risks,
            "hybrid_traits": hybrid_traits
        }

    def _calculate_positive_trait(self, trait_def, label_ids, label_confidences, context):
        required = trait_def.get('required', [])
        optional = trait_def.get('optional', [])
        hard_forbidden = trait_def.get('hard_forbidden', [])
        soft_forbidden = trait_def.get('soft_forbidden', [])
        k_trait = trait_def.get('calculated_k', 1.0)
        
        context_weight = trait_def.get('context_weight', {}).get(context, 1.0)
        
        present_required = [r for r in required if r in label_ids]
        present_optional = [o for o in optional if o in label_ids]
        present_hard = [h for h in hard_forbidden if h in label_ids]
        present_soft = [s['label'] for s in soft_forbidden if s['label'] in label_ids]
        
        if present_hard:
            return 0, []

        # 앵커 게이트: 이 trait 고유의 앵커(unique required)가 하나도 없으면 미점화.
        # 공유 hub 라벨만으로는 trait이 켜지지 않게 해 과호출(over-firing) 차단.
        anchors = trait_def.get('anchor', [])
        if anchors and not any(a in label_ids for a in anchors):
            return 0, []

        req_count = len(present_required)
        req_total = len(required) if required else 0
        req_ratio = req_count / req_total if req_total > 0 else 1.0
        
        if req_ratio < 1.0 and context == "crisis":
            penalty_factor = 0.7
        elif req_ratio < 1.0:
            penalty_factor = 0.5
        else:
            penalty_factor = 1.0
        
        strength_raw = 0.0
        evidence = []
        
        for label_id in present_required:
            conf = label_confidences.get(label_id, 0.5)
            weight = 0.5
            contribution = weight * conf * context_weight * penalty_factor
            strength_raw += contribution
            evidence.append(f"[REQ] {label_id} (w:{weight}, conf:{conf}, ctx:{context_weight}, pf:{penalty_factor})")
        
        if req_ratio >= 0.5:
            for label_id in present_optional:
                conf = label_confidences.get(label_id, 0.5)
                weight = 0.2
                contribution = weight * conf
                strength_raw += contribution
                evidence.append(f"[OPT] {label_id} (w:{weight}, conf:{conf})")
        
        for soft in soft_forbidden:
            if soft['label'] in label_ids:
                penalty = soft['penalty']
                conf = label_confidences.get(soft['label'], 0.5)
                strength_raw -= penalty * conf
                evidence.append(f"[SOFT] -{penalty}: {soft['label']}")
        
        strength_log = math.log(1 + strength_raw) if strength_raw > 0 else 0
        strength_normalized = min(1.0, strength_log / k_trait) if k_trait > 0 else strength_log
        
        return round(strength_normalized, 4), evidence

    def _calculate_negative_trait(self, trait_def, label_ids, label_confidences):
        required = trait_def.get('required', [])
        optional = trait_def.get('optional', [])
        k_trait = trait_def.get('k_trait', 0.9)
        
        present_required = [r for r in required if r in label_ids]

        # 앵커 게이트 (부정 trait도 동일 적용)
        anchors = trait_def.get('anchor', [])
        if anchors and not any(a in label_ids for a in anchors):
            return 0

        if required:
            req_ratio = len(present_required) / len(required)
            if req_ratio < 0.5:
                return 0
        
        severity_raw = 0.0
        for label_id in present_required:
            conf = label_confidences.get(label_id, 0.5)
            weight = 0.5
            severity_raw += weight * conf
        
        for label_id in optional:
            if label_id in label_ids:
                conf = label_confidences.get(label_id, 0.5)
                weight = 0.25
                severity_raw += weight * conf
        
        severity = severity_raw * k_trait
        
        return round(severity, 3)

    def _calculate_confidence(
        self,
        micro_labels,
        label_confidences,
        label_context_list,
        label_count
    ):
        """
        수정사항:
        - consistency: 0.5 고정 → 실계산으로 교체
          공식: label별 (고유 context 수 / 전체 등장 횟수) 의 평균
          의미: 동일 label이 다양한 맥락에서 반복 등장할수록 일관성 높음
               동일 맥락에서만 반복되면 일관성 낮음
        """
        # volume: 데이터 양 기반 점수 (5개 이상이면 최대)
        volume = min(len(micro_labels) / 5, 1.0)

        # avg_nlp_conf: label별 평균 confidence의 전체 평균
        avg_nlp_conf = 0.0
        if label_confidences:
            avg_nlp_conf = sum(label_confidences.values()) / len(label_confidences)

        # consistency: 실계산
        if label_count:
            consistency_scores = []
            for lid, count in label_count.items():
                unique_contexts = len(label_context_list.get(lid, set()))
                if count == 1:
                    # 단일 등장은 일관성 측정 불가 → 중립값 0.5
                    consistency_scores.append(0.5)
                else:
                    score = unique_contexts / count
                    consistency_scores.append(score)
            consistency = round(sum(consistency_scores) / len(consistency_scores), 4)
        else:
            consistency = 0.5

        confidence = (volume * 0.3) + (avg_nlp_conf * 0.5) + (consistency * 0.2)

        return round(confidence, 3)

    def _get_confidence_level(self, confidence):
        if confidence >= 0.75:
            return "high"
        elif confidence >= 0.45:
            return "medium"
        else:
            return "low"

    def _detect_risks(self, micro_labels, positive_traits, negative_traits):
        risks = []
        label_ids = [ml['label_id'] for ml in micro_labels]
        
        negative_count = sum(1 for lid in label_ids if lid.startswith('N'))
        if negative_count >= 2:
            severity = "high" if negative_count >= 4 else "medium"
            risks.append({
                "risk_id": "R01",
                "name": "Toxic Leader",
                "severity": severity,
                "score": min(0.9, 0.3 + (negative_count * 0.15)),
                "reason": f"N-Label {negative_count}개 검출"
            })
        
        if negative_traits:
            max_neg = negative_traits[0]
            if max_neg['strength'] > 0.2:
                risks.append({
                    "risk_id": "R02",
                    "name": f"{max_neg['name']} Dominance",
                    "severity": "high" if max_neg['strength'] > 0.5 else "medium",
                    "score": round(min(1.0, max_neg['strength']), 2),
                    "reason": f"Negative Trait Strength: {max_neg['strength']}"
                })
        
        if any('N30' in lid for lid in label_ids):
            risks.append({
                "risk_id": "R03",
                "name": "Integrity Risk",
                "severity": "medium",
                "score": 0.7,
                "reason": "언행 불일치 (N30-01) 검출"
            })
        
        if any('N28' in lid for lid in label_ids):
            risks.append({
                "risk_id": "R04",
                "name": "Transparency Risk",
                "severity": "high",
                "score": 0.8,
                "reason": "투명성 위반 (N28-01) 검출"
            })
        
        if any('N15-03' in lid for lid in label_ids):
            risks.append({
                "risk_id": "R05",
                "name": "Psychological Safety Risk",
                "severity": "high",
                "score": 0.85,
                "reason": "심리적 안전 파괴 (N15-03) 검출"
            })
        
        return risks

    def _generate_hybrids(self, positive_traits):
        hybrids = []
        
        eligible_traits = [t for t in positive_traits if t['strength'] >= 0.3]
        
        for rule in self.hybrid_rules:
            components = rule.get('components', [])
            if len(components) != 2:
                continue
            
            found = [t for t in eligible_traits if t['trait_id'] in components]
            
            if len(found) == 2:
                avg_strength = (found[0]['strength'] + found[1]['strength']) / 2
                if avg_strength >= 0.5:
                    hybrids.append({
                        "hybrid_id": rule['hybrid_id'],
                        "name": rule['name'],
                        "components": components,
                        "combined_strength": round(avg_strength * rule.get('weight', 1.0), 3)
                    })
        
        return hybrids


def run_test_cases():
    engine = LeadershipEngine()

    with open('data/test/test_cases_v1.json', 'r', encoding='utf-8') as f:
        test_data = json.load(f)

    print("=== 리더십 엔진 테스트 (v2.0 - 3단계 Strength) ===")
    print()

    for case in test_data['evaluation_cases'][:5]:
        print(f"[{case['case_id']}]")
        print(f"텍스트: {case['raw_text'][:50]}...")
        
        context = "normal"
        if "crisis" in case.get('expected_micro_labels', [{}])[0].get('context', 'normal'):
            context = "crisis"
        
        result = engine.process(case['expected_micro_labels'], context=context)
        
        print(f"  Primary: {result['primary']} ({result['primary_name']})")
        print(f"  Strength: {result['primary_strength']}")
        print(f"  Confidence: {result['confidence']} ({result['confidence_level']})")
        print(f"  Secondary: {result['secondary']}")
        print(f"  Trait %: {result['trait_percentages']}")
        print(f"  Negative: {result['negative_traits']}")
        print(f"  Risks: {result['risks']}")
        print(f"  Hybrids: {result['hybrid_traits']}")
        print()


if __name__ == '__main__':
    run_test_cases()