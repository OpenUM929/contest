"""
데이터 검증 모듈
- 라벨 JSON 스키마 검증
- 트레이트 JSON 스키마 검증
"""
import re
from pathlib import Path

PROJECT = Path(__file__).parent.parent

def validate_label(label_data, label_type="positive"):
    """
    라벨 데이터 검증
    label_type: 'positive' or 'negative'
    """
    errors = []
    
    # 1. 필수 필드 확인
    required_fields = ["label_id", "label_name", "macro"]
    for field in required_fields:
        if field not in label_data:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        return False, errors
    
    # 2. label_id 형식 검증
    lid = label_data.get("label_id", "")
    if label_type == "positive":
        pattern = r'^M\d{2}-\d{2}$'
    else:
        pattern = r'^N\d{2}-\d{2}$'
    
    if not re.match(pattern, lid):
        errors.append(f"Invalid label_id format: {lid}")
    
    # 3. weight 범위 검증
    weight = label_data.get("weight", 0.0)
    if not (0.0 <= weight <= 1.0):
        errors.append(f"Weight out of range [0,1]: {weight}")
    
    # 4. context_weight 키 검증
    ctx = label_data.get("context_weight", {})
    valid_keys = {"crisis", "normal", "innovation"}
    if ctx and not set(ctx.keys()).issubset(valid_keys):
        errors.append(f"Invalid context_weight keys: {set(ctx.keys()) - valid_keys}")
    
    return len(errors) == 0, errors

def validate_trait(trait_data):
    """트레이트 데이터 검증"""
    errors = []
    
    # 1. 필수 필드
    required_fields = ["trait_id", "trait_name", "trait_type"]
    for field in required_fields:
        if field not in trait_data:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        return False, errors
    
    # 2. trait_id 형식
    tid = trait_data.get("trait_id", "")
    if not re.match(r'^T\d{2,3}$', tid):
        errors.append(f"Invalid trait_id format: {tid}")
    
    # 3. required/optional 라벨 존재 여부 확인
    all_labels = _load_all_label_ids()
    
    for label_id in trait_data.get("required", []):
        if label_id not in all_labels:
            errors.append(f"Required label not found: {label_id}")
    
    for label_id in trait_data.get("optional", []):
        if label_id not in all_labels:
            errors.append(f"Optional label not found: {label_id}")
    
    return len(errors) == 0, errors

def _load_all_label_ids():
    """모든 라벨 ID 로드 (검증용)"""
    label_ids = set()
    
    for label_type in ["positive", "negative"]:
        src_dir = PROJECT / "data" / "micro_labels" / label_type
        if not src_dir.exists():
            continue
        	# Fallback to unified JSON if individual files don't exist
        fallback = PROJECT / "data" / "micro_labels" / f"{label_type}_micro_labels.json"
        if fallback.exists():
            from src.data_integrator import split_labels
            # Use the unified file
            import json
            with open(fallback, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for label in data.get('micro_labels', []):
                label_ids.add(label.get('label_id'))
        else:
            for json_file in src_dir.glob("*.json"):
                import json
                with open(json_file, 'r', encoding='utf-8') as f:
                    label = json.load(f)
                    label_ids.add(label.get('label_id'))
    
    return label_ids

def validate_and_save_label(label_data, label_type, label_id):
    """검증 후 저장"""
    is_valid, errors = validate_label(label_data, label_type)
    if not is_valid:
        return False, errors
    
    # 저장
    from src.backup_manager import create_backup
    file_path = PROJECT / "data" / "micro_labels" / label_type / f"{label_id}.json"
    
    if file_path.exists():
        create_backup(file_path)
    
    import json
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(label_data, f, ensure_ascii=False, indent=2)
    
    return True, ["Saved successfully"]

def validate_and_save_trait(trait_data):
    """검증 후 트레이트 저장"""
    is_valid, errors = validate_trait(trait_data)
    if not is_valid:
        return False, errors
    
    from src.backup_manager import create_backup
    tid = trait_data.get("trait_id")
    ttype = "positive" if (tid.startswith('T1') and len(tid) == 3) else "negative"
    
    file_path = PROJECT / "data" / "traits" / ttype / f"{tid}.json"
    
    if file_path.exists():
        create_backup(file_path)
    
    import json
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(trait_data, f, ensure_ascii=False, indent=2)
    
    return True, ["Saved successfully"]
