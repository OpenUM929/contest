from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), env_file_encoding="utf-8")

    database_url: str = "postgresql+asyncpg://ium:ium_secret@localhost:5432/ium"
    redis_url: str = "redis://localhost:6379"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    public_data_api_key: str = ""          # 공공데이터포털 API 키 (국가기록원)
    kcisa_api_key: str = ""                # KCISA 문화공공데이터광장 API 키 (민속박물관)
    cheongju_museum_api_key: str = ""      # 국립청주박물관_소장품 API 키 (이미지 제공)
    deepseek_api_key: str = ""             # 딥시크 API 키 (질문 생성)
    opencode_base_url: str = "https://opencode.ai/zen/v1"  # OpenCode Zen API
    opencode_api_key: str = ""             # OpenCode API 키
    opencode_model: str = "big-pickle"      # OpenCode 사용 모델명
    environment: str = "development"

    # Phase 3 전환용 (비어있으면 기존 API 사용)
    clova_client_id: str = ""
    clova_client_secret: str = ""
    use_hyperclovax: bool = False

    # 미디어 캐시 설정
    media_cache_dir: str = "/tmp/ium_media"

    # SMTP 이메일 발송
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    welfare_notify_email: str = ""

    # 로컬 개발용
    skip_emotion: bool = False  # 감정 모델 로딩 생략

    # 복지사 API 키 암호화 (운영: 환경변수 IUM_API_KEY_ENCRYPTION_KEY 권장)
    ium_api_key_encryption_key: str = ""


settings = Settings()
