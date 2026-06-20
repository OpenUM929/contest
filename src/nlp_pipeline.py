"""
리더십 성향 추론 엔진 / NLP Micro Label 추출 파이프라인 v2.0

특징:
- 구글 제미나이 기반
- Confidence Calibration 지원
- 중복 문장 제거
- 문장 중요도 가중치
- Hallucination 방지 검증 레이어
- 오류 피드백 리트라이 시스템
"""
import json
import os
from difflib import SequenceMatcher
from typing import Dict, Set, Tuple, List, Optional, Callable

from dotenv import load_dotenv
from openai import OpenAI
try:
    from google import genai
except ImportError:
    # Fallback to old API if new package not available
    import google.generativeai as genai

# .env 파일 자동 로드
load_dotenv()


# -----------------------------------------------------------------------------
# 기본 상수 정의
# -----------------------------------------------------------------------------
# MAX_LABEL_PER_SENTENCE = 2  # 제거됨: 수량 제한 없이 모든 관련 label 추출
DEFAULT_CONF_THRESHOLD = 0.5
DEFAULT_DEDUP_THRESHOLD = 0.8
DEFAULT_MAX_RETRY = 3
DEFAULT_CALIBRATION_BASE = 0.88
DEFAULT_SENTENCE_WEIGHT = 1.0
IMPORTANCE_WEIGHT = 1.2

IMPORTANCE_KEYWORDS = [
    "특히", "항상", "주로", "결국", "가장", "반드시", "절대", "핵심",
    "매우", "정말", "심지어", "결정적으로", "근본적으로"
]

ALLOWED_CONTEXTS = {"crisis", "normal", "innovation"}


# -----------------------------------------------------------------------------
# Step 1. Micro Label 허용 목록 로더
# -----------------------------------------------------------------------------
def load_allowed_labels(label_schema: Dict) -> tuple[Set[str], Dict[str, str]]:
    """
    label_schema에서 허용된 Micro Label ID 목록을 set으로 추출
    검증 시 O(1) 접근을 위해 set 사용
    동시에 ID → 이름 매핑 딕셔너리도 반환 (프롬프트용)
    """
    allowed = set()
    label_name_map = {}
    
    for item in label_schema["labels"]:
        for micro in item.get("micro_labels", []):
            if isinstance(micro, dict):
                label_id = micro.get("label_id")
                label_name = micro.get("label_name", "")
                if label_id:
                    allowed.add(label_id)
                    if label_name:
                        label_name_map[label_id] = label_name
            else:
                allowed.add(micro)
    
    return allowed, label_name_map


# -----------------------------------------------------------------------------
# Step 2. 프롬프트 생성기
# -----------------------------------------------------------------------------
def build_llm_prompt(user_input: str, allowed_labels: Set[str], label_name_map: Dict[str, str] = None, 
                      grouped_labels: Dict[str, list] = None) -> str:
    """
    제미나이에 전달할 표준 프롬프트 생성
    JSON 이스케이프, 허용 레이블 목록, 규칙 명시 포함
    
    Args:
        user_input: 분석할 텍스트
        allowed_labels: 허용된 label_id set
        label_name_map: label_id → label_name 매핑
        grouped_labels: {카테고리: [label_id, ...]} 형태의 그룹화된 라벨
    """
    # 라벨 목록 포맷팅
    if grouped_labels:
        # 카테고리별 그룹화 형식
        label_parts = []
        for category, label_ids in grouped_labels.items():
            label_ids = [lid for lid in label_ids if lid in allowed_labels]
            if label_ids:
                labels_str = ", ".join([f"{lid}: {label_name_map.get(lid, '')}" if label_name_map.get(lid) else lid 
                                       for lid in label_ids])
                label_parts.append(f"【{category}】\n{labels_str}")
        label_text = "\n\n".join(label_parts)
    elif label_name_map:
        # 기존 방식: ID + 이름 형식
        label_list = []
        for label_id in sorted(allowed_labels):
            name = label_name_map.get(label_id, "")
            if name:
                label_list.append(f"{label_id}: {name}")
            else:
                label_list.append(label_id)
        label_text = ", ".join(label_list)
    else:
        label_text = ", ".join(sorted(allowed_labels))

    prompt = f"""당신은 리더십 행동을 분석하여 Micro Label로 변환하는 시스템입니다.
 
[절대 규칙]
- 순수 JSON만 출력 (코드블록 금지, 설명 금지)
- label_id는 반드시 제공된 목록에서만 선택
- 각 문장을 sentences 배열로 구성
 
[context 판단]
- crisis: 갈등, 압력, 위기 상황
- normal: 일반 협업
- innovation: 창의/변화 중심 (맥락 불분명시 종합 판단)
 
[confidence 기준]
- 0.9+: 명확히 직접 언급
- 0.7~0.89: 강한 추론
- 0.5~0.69: 합리적 추론
- 0.5 미만: 금지
 
[라벨 충돌 해결 규칙]
- 동일 문장에 긍정/부정 라벨 키워드가 혼재될 경우, 텍스트의 최종 결론(결과)을 기준으로 판별한다.
- 최종 결과가 긍정이면 긍정 라벨을, 부정이면 부정 라벨을 우선 부여한다.
- 예: "서버 다운(부정)이 발생했으나, 10분 만에 완벽히 복구(긍정)되었다" → 최종 결과가 긍정이므로 M20-01(위기 대응) 우선 부여
 
[출력 형식]
{{ 
  "sentences": [
    {{
      "text": "문장 원문",
      "context": "innovation",
      "labels": [
        {{
          "label_id": "M03-03",
          "confidence": 0.95,
          "reason": "핵심 근거"
        }}
      ]
    }}
  ]
}}
 
[참고]
혁신/창의 상황에서는 M03, M05, M23, M26 계열을 고려하세요.
비전 제시 상황에서는 M01 계열을 고려하세요.
동기부여 상황에서는 M02 계열을 고려하세요.

[사용 가능한 Micro Label 목록]
{label_text}

[입력 텍스트]
{user_input}"""
    return prompt


# -----------------------------------------------------------------------------
# Step 3. 구조 검증기
# -----------------------------------------------------------------------------
def validate_structure(data: Dict, allowed_labels: Set[str]) -> Tuple[bool, str]:
    """
    LLM 출력이 규격에 맞는지 검증
    Hallucination 방지를 위한 가장 중요한 레이어
    """
    if "sentences" not in data:
        return False, "sentences 키가 없음"

    for i, s in enumerate(data["sentences"]):
        if "text" not in s:
            return False, f"sentences[{i}]: text 필드 없음"
        if "labels" not in s:
            return False, f"sentences[{i}]: labels 필드 없음"
        if "context" not in s:
            return False, f"sentences[{i}]: context 필드 없음"
        if s["context"] not in ALLOWED_CONTEXTS:
            return False, f"sentences[{i}]: context 값 오류 ({s['context']})"

        for j, l in enumerate(s["labels"]):
            if "label_id" not in l:
                return False, f"sentences[{i}].labels[{j}]: label_id 없음"
            if "confidence" not in l:
                return False, f"sentences[{i}].labels[{j}]: confidence 없음"
            # reason은 선택적 필드
            
            # confidence 타입 정규화 (str → float)
            try:
                conf_value = float(l["confidence"])
            except (TypeError, ValueError):
                return False, f"sentences[{i}].labels[{j}]: confidence 타입 오류 ({l['confidence']})"
            
            if l["label_id"] not in allowed_labels:
                return False, f"sentences[{i}].labels[{j}]: 허용되지 않은 label_id ({l['label_id']})"
            if not (0.0 <= conf_value <= 1.0):
                return False, f"sentences[{i}].labels[{j}]: confidence 범위 오류 ({conf_value})"

    return True, "ok"


# -----------------------------------------------------------------------------
# Step 4. OpenCode LLM 래퍼
# -----------------------------------------------------------------------------
def create_opencode_client(
    api_key: Optional[str] = None,
    base_url: str = "https://opencode.ai/zen",
    model: str = "big-pickle"
) -> Callable[[str], str]:
    """
    OpenCode API 클라이언트 생성
    OpenCode Zen 서버 (big-pickle 무료 모델)
    """
    if api_key is None:
        api_key = os.getenv("OPENCODE_API_KEY")
    
    if not api_key:
        raise ValueError("OPENCODE_API_KEY 환경변수가 설정되지 않았습니다")

    client = OpenAI(
        base_url=f"{base_url}/v1",
        api_key=api_key,
    )

    def llm_call(prompt: str) -> str:
        response = client.chat.completions.create(
            model=model,
            temperature=0.0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=8192
        )
        return response.choices[0].message.content.strip()

    return llm_call


# -----------------------------------------------------------------------------
# Step 5. LLM 호출 + retry + 오류 피드백
# -----------------------------------------------------------------------------
def call_llm_with_retry(
    llm: Callable[[str], str],
    prompt: str,
    allowed_labels: Set[str],
    max_retry: int = DEFAULT_MAX_RETRY
) -> Dict:
    """
    단순 retry가 아닌 실패 원인을 다음 시도에 피드백으로 전달
    동일 오류 반복 발생을 크게 감소시킴
    """
    feedback = ""

    for attempt in range(max_retry):
        full_prompt = prompt + feedback
        response = llm(full_prompt)

        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            feedback = (
                f"\n\n[오류 피드백 - 시도 {attempt + 1}]"
                "\nJSON 파싱 실패. 다음을 반드시 지킬 것:"
                "\n- JSON 외 텍스트 절대 금지"
                "\n- 코드블록(```) 사용 금지"
                "\n- 순수 JSON만 출력"
            )
            continue

        is_valid, error_msg = validate_structure(data, allowed_labels)
        if is_valid:
            return data
        else:
            feedback = (
                f"\n\n[오류 피드백 - 시도 {attempt + 1}]"
                f"\n구조 검증 실패: {error_msg}"
                "\n다음을 반드시 지킬 것:"
                "\n- label_id는 반드시 제공된 목록에서만 선택"
                "\n- context는 crisis / normal / innovation 중 하나"
                "\n- confidence는 0.0~1.0 사이 실수"
                "\n- reason은 선택적 필드 (있어도 되고 없어도 됨)"
            )

    raise Exception(f"LLM 추출 실패: {max_retry}회 시도 후에도 유효한 JSON 미반환")


# -----------------------------------------------------------------------------
# Step 6. Confidence Calibration
# -----------------------------------------------------------------------------
def calibrate_confidence(
    label_id: str,
    raw_conf: float,
    calibration_map: Dict[str, float]
) -> float:
    """
    LLM이 과대 추정하는 confidence를 경험적 계수로 보정
    레이블 별 개별 계수 지원, 미설정시 기본값 0.88 적용
    """
    base_factor = calibration_map.get(label_id, DEFAULT_CALIBRATION_BASE)
    return round(raw_conf * base_factor, 4)


def apply_calibration(data: Dict, calibration_map: Dict[str, float]) -> Dict:
    for sentence in data["sentences"]:
        for label in sentence["labels"]:
            label["confidence"] = calibrate_confidence(
                label["label_id"],
                label["confidence"],
                calibration_map
            )
    return data


# -----------------------------------------------------------------------------
# Step 7. Low Confidence 필터
# -----------------------------------------------------------------------------
def filter_low_confidence(data: Dict, threshold: float = DEFAULT_CONF_THRESHOLD) -> Dict:
    """
    Calibration 후 임계값 미만 label 제거
    label이 전부 제거된 문장은 문장째 제거
    """
    filtered_sentences = []

    for sentence in data["sentences"]:
        valid_labels = []
        for l in sentence["labels"]:
            try:
                conf = float(l.get("confidence", 0))
            except (TypeError, ValueError):
                continue
            if conf >= threshold:
                valid_labels.append(l)
        if valid_labels:
            sentence["labels"] = valid_labels
            filtered_sentences.append(sentence)

    data["sentences"] = filtered_sentences
    return data


# -----------------------------------------------------------------------------
# Step 8. 중복 문장 제거
# -----------------------------------------------------------------------------
def is_similar(a: str, b: str, threshold: float = DEFAULT_DEDUP_THRESHOLD) -> bool:
    return SequenceMatcher(None, a, b).ratio() > threshold


def deduplicate_sentences(data: Dict, threshold: float = DEFAULT_DEDUP_THRESHOLD) -> Dict:
    """
    의미적으로 중복되는 문장 제거
    먼저 등장한 문장을 우선 유지
    """
    result = []
    for sentence in data["sentences"]:
        is_dup = any(
            is_similar(sentence["text"], kept["text"], threshold)
            for kept in result
        )
        if not is_dup:
            result.append(sentence)

    data["sentences"] = result
    return data


# -----------------------------------------------------------------------------
# Step 9. Mutual Exclusion (객관적 처리 - Negative 우선 규칙 제거)
# -----------------------------------------------------------------------------
MUTUAL_EXCLUSION_PAIRS = {
    "M14": ["N14-01", "N14-02", "N14-03"],
    "M08": ["N08-01", "N08-02", "N08-03"],
    "M15": ["N15-01", "N15-02", "N15-03", "N15-04", "N15-05", "N15-06"],
    "M33": ["N33-01", "N33-02"],
    "M30": ["N30-01"],
}


def resolve_mutual_exclusion(data: Dict) -> Dict:
    """
    Positive + Negative 라벨이 동시에 존재하는 경우 모두 보존
    기존의 Negative 우선 규칙을 제거하여 객관적 분석 가능하도록 함
    """
    # 互斥処理ロジックを無効化 - 全ラベルを維持してトレイト計算に反映
    return data


# -----------------------------------------------------------------------------
# Step 9. 문장 중요도 Weight 부여
# -----------------------------------------------------------------------------
def assign_sentence_weight(sentence_text: str) -> float:
    if any(k in sentence_text for k in IMPORTANCE_KEYWORDS):
        return IMPORTANCE_WEIGHT
    return DEFAULT_SENTENCE_WEIGHT


def apply_sentence_weights(data: Dict) -> Dict:
    for sentence in data["sentences"]:
        sentence["sentence_weight"] = assign_sentence_weight(sentence["text"])
    return data


# -----------------------------------------------------------------------------
# Step 10. Label per Sentence 상한 적용 (비활성화됨)
# -----------------------------------------------------------------------------
# def apply_label_cap(data: Dict, max_labels: int = MAX_LABEL_PER_SENTENCE) -> Dict:
#     """
#     문장당 label 개수 상한 적용
#     confidence 높은 순으로 상위 N개만 유지
#     프롬프트에서 지시해도 지키지 않는 경우 대비 하드 컷
#     """
#     for sentence in data["sentences"]:
#         if len(sentence["labels"]) > max_labels:
#             sentence["labels"] = sorted(
#                 sentence["labels"],
#                 key=lambda l: l["confidence"],
#                 reverse=True
#             )[:max_labels]
#     return data


# -----------------------------------------------------------------------------
# Step 11. Conflict 감지
# -----------------------------------------------------------------------------
def detect_conflicts(
    extracted: Dict,
    conflict_axis_map: Dict[str, str]
) -> List[Dict]:
    """
    동일 축에서 긍정/부정 레이블이 동시 검출된 경우 conflict 판정
    동일 문장 → Hard Conflict, 다른 문장 → Soft Conflict
    """
    conflicts = []
    axis_seen = {}

    for i, sentence in enumerate(extracted["sentences"]):
        for label in sentence["labels"]:
            label_id = label["label_id"]
            axis = conflict_axis_map.get(label_id)
            if axis is None:
                continue

            label_type = "M" if label_id.startswith("M") else "N"

            if axis not in axis_seen:
                axis_seen[axis] = []
            axis_seen[axis].append((i, label_type))

    for axis, occurrences in axis_seen.items():
        types_seen = set(t for _, t in occurrences)
        if "M" not in types_seen or "N" not in types_seen:
            continue

        m_indices = [idx for idx, t in occurrences if t == "M"]
        n_indices = [idx for idx, t in occurrences if t == "N"]

        hard = any(idx in n_indices for idx in m_indices)

        conflicts.append({
            "axis": axis,
            "type": "hard" if hard else "soft",
            "m_sentence_indices": m_indices,
            "n_sentence_indices": n_indices
        })

    return conflicts


# -----------------------------------------------------------------------------
# 전체 파이프라인 통합 (하이브리드: Vector DB + LLM with Threshold)
# -----------------------------------------------------------------------------
def run_extraction_pipeline(
    user_input: str,
    label_schema: Dict,
    conflict_axis_map: Dict[str, str],
    llm: Optional[Callable[[str], str]] = None,
    calibration_map: Optional[Dict[str, float]] = None,
    conf_threshold: float = DEFAULT_CONF_THRESHOLD,
    dedup_threshold: float = DEFAULT_DEDUP_THRESHOLD,
    max_retry: int = DEFAULT_MAX_RETRY,
    vector_searcher: Optional[object] = None
) -> Dict:
    """
    NLP 추출 파이프라인 전체 실행 엔트리 포인트 (하이브리드 버전)
    
    Args:
        user_input: 분석할 사용자 입력 텍스트
        label_schema: Micro Label 스키마
        conflict_axis_map: Label → 축 매핑 테이블
        llm: LLM 호출 함수 (없으면 제미나이 기본 클라이언트 생성)
        calibration_map: confidence 보정 계수 맵
        conf_threshold: low confidence 제거 임계값
        dedup_threshold: 중복 문장 판정 유사도
        max_retry: LLM 호출 최대 재시도 횟수
        vector_searcher: Vector DB 검색기 (없으면 LLM만 사용)
    
    Returns:
        추출 결과, 충돌 목록, 메타데이터를 포함한 딕셔너리
    """
    if calibration_map is None:
        calibration_map = {}
    
    if llm is None:
        llm = create_gemini_client()
    
    # 1. 허용 레이블 로드
    allowed_labels, label_name_map = load_allowed_labels(label_schema)
    
    # 2. Vector DB 검색 (제공된 경우)
    vector_results = None
    should_call_llm = True
    vector_reason = "Vector DB 없음"
    
    if vector_searcher:
        # Vector DB 검색 with Threshold 로직
        vector_output = vector_searcher.search_with_threshold(user_input, k=15, expand=True)
        vector_results = vector_output['results']
        should_call_llm = vector_output['should_call_llm']
        vector_reason = vector_output['reason']
        
        # 고신뢰도: LLM 건너뛰기, Vector DB 결과 직접 사용
        # 저신뢰도: 빈 결과 반환 (매칭 없음)
        if not should_call_llm and vector_results and '고신뢰도' in vector_reason:
            # Vector DB 결과를 표준 포맷으로 변환
            sentences = [{
                "text": user_input,
                "context": "normal",  # 기본 컨텍스트
                "labels": [
                    {
                        "label_id": r['label_id'],
                        "confidence": r['confidence'],
                        "reason": f"Vector DB 고신뢰도 ({r['confidence']:.2f})"
                    }
                    for r in vector_results[:5]  # 상위 5개만
                ],
                "sentence_weight": 1.0
            }]
            
            extracted = {"sentences": sentences}
            
            # Confidence Calibration (Vector DB 결과에도 적용)
            extracted = apply_calibration(extracted, calibration_map)
            
            # Conflict 감지
            conflicts = detect_conflicts(extracted, conflict_axis_map)
            
            # Mutual Exclusion 처리
            extracted = resolve_mutual_exclusion(extracted)
            
            total_sentences = len(extracted["sentences"])
            total_labels = sum(len(s["labels"]) for s in extracted["sentences"])
            
            return {
                "extracted": extracted,
                "conflicts": conflicts,
                "meta": {
                    "total_sentences": total_sentences,
                    "total_labels": total_labels,
                    "conflict_count": len(conflicts),
                    "vector_only": True,
                    "vector_reason": vector_reason
                }
            }
    
    # 3. LLM 호출 (필요한 경우만)
    if should_call_llm or not vector_searcher:
        # 프롬프트 생성
        prompt = build_llm_prompt(user_input, allowed_labels, label_name_map)
        
        # Vector DB 결과가 있으면 프롬프트에 참고 정보 추가
        if vector_results:
            vector_context = "\n[Vector DB 검색 결과 참고]\n" + "\n".join([
                f"- {r['label_id']} (신뢰도: {r['confidence']:.2f})"
                for r in vector_results[:10]
            ])
            prompt += vector_context
        
        # LLM 호출 + 검증
        extracted = call_llm_with_retry(llm, prompt, allowed_labels, max_retry)
        
        # 4. Confidence Calibration
        extracted = apply_calibration(extracted, calibration_map)
        
        # 5. Low confidence 제거
        extracted = filter_low_confidence(extracted, conf_threshold)
        
        # 6. 중복 문장 제거
        extracted = deduplicate_sentences(extracted, dedup_threshold)
        
        # 7. 문장 중요도 Weight 부여
        extracted = apply_sentence_weights(extracted)
        
        # 8. Conflict 감지
        conflicts = detect_conflicts(extracted, conflict_axis_map)
        
        # 9. Mutual Exclusion 처리
        extracted = resolve_mutual_exclusion(extracted)
        
        total_sentences = len(extracted["sentences"])
        total_labels = sum(len(s["labels"]) for s in extracted["sentences"])
        
        return {
            "extracted": extracted,
            "conflicts": conflicts,
            "meta": {
                "total_sentences": total_sentences,
                "total_labels": total_labels,
                "conflict_count": len(conflicts),
                "vector_only": False,
                "vector_reason": vector_reason,
                "used_llm": True
            }
        }
    
    # Vector DB 결과도 없고 LLM도 호출하지 않는 경우
    return {
        "extracted": {"sentences": []},
        "conflicts": [],
        "meta": {
            "total_sentences": 0,
            "total_labels": 0,
            "conflict_count": 0,
            "vector_only": False,
            "vector_reason": "저신뢰도 - 매칭 없음",
            "used_llm": False
        }
    }