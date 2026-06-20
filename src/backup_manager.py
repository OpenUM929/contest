"""
백업 관리 모듈
- 수정 전 자동 백업
- 백업 목록 조회
- 특정 버전으로 복원
"""
import json
import shutil
from datetime import datetime
from pathlib import Path

PROJECT = Path(__file__).parent.parent
BACKUP_DIR = PROJECT / "data" / "backups"

def ensure_backup_dir():
    """백업 디렉토리 확인/생성"""
    BACKUP_DIR.mkdir(exist_ok=True)
    return BACKUP_DIR

def create_backup(file_path):
    """
    파일 수정 전 백업 생성
    file_path: Path 객체 또는 문자열
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return None
    
    # 타임스탬프 생성
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{file_path.stem}_{ts}{file_path.suffix}"
    
    # 백업 대상 디렉토리 결정
    rel_path = file_path.relative_to(PROJECT)
    if "micro_labels" in str(rel_path):
        backup_dir = PROJECT / "data" / "micro_labels" / "backups"
    elif "traits" in str(rel_path):
        backup_dir = PROJECT / "data" / "traits" / "backups"
    else:
        backup_dir = BACKUP_DIR
    
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / backup_name
    
    # 복사
    shutil.copy2(file_path, backup_path)
    
    # 이력 기록
    history_file = BACKUP_DIR / "backup_history.json"
    history = []
    if history_file.exists():
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
    
    history.append({
        "timestamp": ts,
        "original": str(rel_path),
        "backup": str(backup_path.relative_to(PROJECT)),
        "action": "auto_backup"
    })
    
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    
    return str(backup_path)

def list_backups(target_type="labels"):
    """백업 목록 조회"""
    if target_type == "labels":
        backup_dir = PROJECT / "data" / "micro_labels" / "backups"
    elif target_type == "traits":
        backup_dir = PROJECT / "data" / "traits" / "backups"
    else:
        backup_dir = BACKUP_DIR
    
    if not backup_dir.exists():
        return []
    
    backups = []
    for f in sorted(backup_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        backups.append({
            "name": f.name,
            "path": str(f),
            "size": f.stat().st_size,
            "mtime": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
        })
    
    return backups

def restore_backup(backup_path):
    """특정 백업 파일로 복원"""
    backup_path = Path(backup_path)
    if not backup_path.exists():
        return False, "Backup file not found"
    
    # 원본 경로 추론
    name_parts = backup_path.stem.split("_")
    # 마지막 두 개(날짜, 시간) 제거하면 원본 파일명
    original_name = "_".join(name_parts[:-2]) + backup_path.suffix
    
    if "micro_labels" in str(backup_path):
        original_path = PROJECT / "data" / "micro_labels" / original_name
    elif "traits" in str(backup_path):
        original_path = PROJECT / "data" / "traits" / original_name
    else:
        return False, "Cannot determine original path"
    
    # 현재 파일 백업 후 복원
    if original_path.exists():
        create_backup(original_path)
    
    shutil.copy2(backup_path, original_path)
    return True, f"Restored to {original_path}"
