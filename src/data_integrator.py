"""
데이터 통합 및 분할 모듈
- 기존 통합 JSON → 개별 파일 분할 (split)
- 개별 파일 → 통합 JSON 생성 (integrate)
"""
import json
import os
from datetime import datetime
from pathlib import Path

PROJECT = Path(__file__).parent.parent
DATA_DIR = PROJECT / "data"

def split_labels():
    """기존 통합 JSON을 개별 파일로 분할 (마이그레이션)"""
    results = {"positive": 0, "negative": 0}
    
    for label_type in ["positive", "negative"]:
        src_file = DATA_DIR / "micro_labels" / f"{label_type}_micro_labels.json"
        dest_dir = DATA_DIR / "micro_labels" / label_type
        dest_dir.mkdir(exist_ok=True)
        
        if not src_file.exists():
            print(f"[WARN] {src_file} not found, skipping...")
            continue
        
        with open(src_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for label in data.get('micro_labels', []):
            lid = label.get('label_id')
            if not lid:
                continue
            
            # 개별 파일 저장
            out_file = dest_dir / f"{lid}.json"
            with open(out_file, 'w', encoding='utf-8') as f:
                json.dump(label, f, ensure_ascii=False, indent=2)
            results[label_type] += 1
        
        print(f"[OK] {label_type}: {results[label_type]} files → {dest_dir}")
    
    return results

def split_traits():
    """기존 트레이트 JSON을 개별 파일로 분할"""
    results = {"positive": 0, "negative": 0}
    
    src_file = DATA_DIR / "traits" / "trait_definitions.json"
    if not src_file.exists():
        print(f"[WARN] {src_file} not found")
        return results
    
    with open(src_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for trait in data.get('traits', []):
        tid = trait.get('trait_id')
        if not tid:
            continue
        
        # positive/negative 구분
        if tid.startswith('T1') and len(tid) == 3:
            folder = "positive"
        else:
            folder = "negative"
        
        dest_dir = DATA_DIR / "traits" / folder
        dest_dir.mkdir(exist_ok=True)
        
        out_file = dest_dir / f"{tid}.json"
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(trait, f, ensure_ascii=False, indent=2)
        results[folder] += 1
    
    print(f"[OK] Traits: {results}")
    return results

def integrate_labels():
    """개별 라벨 파일들을 통합하여 temp/integrated_data.json 생성"""
    integrated = {
        "generated_at": datetime.now().isoformat(),
        "schema_version": "2026-04-v3",
        "positive_labels": [],
        "negative_labels": []
    }
    
    for label_type in ["positive", "negative"]:
        src_dir = DATA_DIR / "micro_labels" / label_type
        if not src_dir.exists():
            continue
        
        for json_file in sorted(src_dir.glob("*.json")):
            with open(json_file, 'r', encoding='utf-8') as f:
                label_data = json.load(f)
                integrated[f"{label_type}_labels"].append(label_data)
    
    # 통합 파일 저장
    out_dir = PROJECT / "temp"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / "integrated_data.json"
    
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(integrated, f, ensure_ascii=False, indent=2)
    
    print(f"[OK] Integrated file generated: {out_file}")
    print(f"  - Positive labels: {len(integrated['positive_labels'])}")
    print(f"  - Negative labels: {len(integrated['negative_labels'])}")
    
    return str(out_file)

def integrate_traits():
    """개별 트레이트 파일들을 통합 데이터에 추가"""
    integrated_file = PROJECT / "temp" / "integrated_data.json"
    
    # 기존 통합 파일 읽기
    if integrated_file.exists():
        with open(integrated_file, 'r', encoding='utf-8') as f:
            integrated = json.load(f)
    else:
        integrated = {"generated_at": datetime.now().isoformat(), "traits": []}
    
    integrated["traits"] = []
    
    for trait_type in ["positive", "negative"]:
        src_dir = DATA_DIR / "traits" / trait_type
        if not src_dir.exists():
            continue
        
        for json_file in sorted(src_dir.glob("*.json")):
            with open(json_file, 'r', encoding='utf-8') as f:
                trait_data = json.load(f)
                integrated["traits"].append(trait_data)
    
    integrated["generated_at"] = datetime.now().isoformat()
    
    with open(integrated_file, 'w', encoding='utf-8') as f:
        json.dump(integrated, f, ensure_ascii=False, indent=2)
    
    print(f"[OK] Traits added to integrated file: {len(integrated['traits'])} traits")
    return str(integrated_file)

def full_integrate():
    """라벨 + 트레이트 전체 통합"""
    integrate_labels()
    integrate_traits()
    return str(PROJECT / "temp" / "integrated_data.json")

if __name__ == "__main__":
    print("=== Starting Migration ===")
    print("1. Splitting labels...")
    split_labels()
    print("2. Splitting traits...")
    split_traits()
    print("3. Generating integrated file...")
    full_integrate()
    print("=== Done ===")
