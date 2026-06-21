"""복지사 AI API 키 암호화 저장소.

복지사(WelfareWorker)별로 Claude/OpenAI/Gemini API 키와 활성 제공자를
Fernet(AES-256-CBC + HMAC)으로 암호화하여 단일 파일에 보관한다.

저장 구조(복호화 후 JSON):
{
  "<welfare_id>": {
    "claude": "...", "openai": "...", "gemini": "...",
    "active_provider": "claude"
  },
  ...
}

⚠️ 보안 한계: 자동 생성되는 .api_key_encryption_key 파일은 암호문과 동일
디렉터리에 놓이므로 파일시스템 접근이 뚫리면 사실상 평문과 같다. 운영 환경에서는
반드시 환경변수 IUM_API_KEY_ENCRYPTION_KEY 를 사용한다.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings

PROVIDERS = ("claude", "openai", "gemini")

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent  # app/services -> app -> backend
_DATA_FILE = _BACKEND_DIR / "data" / "api_keys.enc"
_KEY_FILE = _BACKEND_DIR / ".api_key_encryption_key"

# load->merge->save 사이의 lost update 방지용. 파일 IO가 동기이므로 스레드 락으로 직렬화한다.
_lock = threading.Lock()
_cipher: Fernet | None = None


def _ensure_key() -> bytes:
    """암호화 키를 우선순위(환경변수 → 키 파일 → 자동 생성)대로 로드/생성한다."""
    # 1. 환경변수(settings) — 운영 권장
    if settings.ium_api_key_encryption_key:
        return settings.ium_api_key_encryption_key.encode()
    # 2. 키 파일(개발)
    if _KEY_FILE.exists():
        return _KEY_FILE.read_bytes().strip()
    # 3. 최초 실행 시 자동 생성
    key = Fernet.generate_key()
    _KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    _KEY_FILE.write_bytes(key)
    return key


def _get_cipher() -> Fernet:
    global _cipher
    if _cipher is None:
        _cipher = Fernet(_ensure_key())
    return _cipher


def _file_path() -> Path:
    return _DATA_FILE


def load_all() -> dict:
    """암호화 파일 → 복호화 → 전체 dict. 파일이 없거나 손상 시 빈 dict."""
    path = _file_path()
    if not path.exists():
        return {}
    try:
        raw = _get_cipher().decrypt(path.read_bytes())
        return json.loads(raw.decode("utf-8"))
    except (InvalidToken, ValueError, json.JSONDecodeError) as e:
        print(f"[ApiKeyStore] 복호화/파싱 실패(빈 dict 반환): {e!r}")
        return {}


def save_all(data: dict) -> None:
    """전체 dict → 암호화 → 파일 저장."""
    path = _file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    token = _get_cipher().encrypt(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    path.write_bytes(token)


def get_worker_keys(welfare_id: str) -> dict:
    """특정 복지사 키 dict. 없으면 빈 dict."""
    if not welfare_id:
        return {}
    return load_all().get(welfare_id, {})


def _normalize(entry: dict) -> dict:
    """빈 키 제거 후 active_provider 정합성을 맞춘다.
    - active_provider가 빈 키를 가리키면 초기화
    - 비어있지 않은 키가 정확히 1개면 active_provider를 그 제공자로 자동 설정
      (프론트가 라디오를 2개 이상일 때만 노출하므로, 이 규칙이 없으면 키 1개만 등록한
       복지사의 키가 사용되지 않고 시스템 fallback으로 빠진다.)
    """
    keys = {p: (entry.get(p) or "").strip() for p in PROVIDERS}
    present = [p for p in PROVIDERS if keys[p]]
    active = (entry.get("active_provider") or "").strip()

    if active not in present:
        active = ""
    if not active and len(present) == 1:
        active = present[0]

    return {**keys, "active_provider": active}


def set_worker_keys(welfare_id: str, keys: dict) -> dict:
    """특정 복지사 키를 저장(merge)하고 정규화된 entry를 반환한다.

    프론트는 마스킹된 키만 보유하므로 기존 키를 그대로 재전송할 수 없다. 따라서
    **빈 문자열로 온 provider 키는 '변경 없음'으로 보고 기존 값을 유지**한다
    (활성 제공자만 바꿀 때 다른 키가 지워지는 사고 방지). active_provider는 항상 갱신한다.
    """
    with _lock:
        data = load_all()
        merged = dict(data.get(welfare_id, {}))
        for p in PROVIDERS:
            val = (keys.get(p) or "").strip()
            if val:
                merged[p] = val
        if "active_provider" in keys:
            merged["active_provider"] = (keys.get("active_provider") or "").strip()
        entry = _normalize(merged)
        data[welfare_id] = entry
        save_all(data)
    return entry


def resolve_active(welfare_id: str | None) -> tuple[str, str] | None:
    """복지사의 활성 (provider, api_key)를 반환. 없으면 None.

    active_provider가 비어 있더라도 비어있지 않은 키가 정확히 1개면 그 키를 사용(방어 로직).
    """
    if not welfare_id:
        return None
    entry = _normalize(get_worker_keys(welfare_id))
    provider = entry["active_provider"]
    if provider and entry.get(provider):
        return provider, entry[provider]
    return None


def mask_key(key: str) -> str:
    """응답용 마스킹: 마지막 4자리만 노출. 8자 미만이면 전체 마스킹."""
    if not key:
        return ""
    if len(key) < 8:
        return "*" * len(key)
    return "*" * (len(key) - 4) + key[-4:]


def get_masked(welfare_id: str) -> dict:
    """GET 응답용: 마스킹된 키 + active_provider."""
    entry = _normalize(get_worker_keys(welfare_id))
    return {
        "claude": mask_key(entry["claude"]),
        "openai": mask_key(entry["openai"]),
        "gemini": mask_key(entry["gemini"]),
        "active_provider": entry["active_provider"],
    }
