"""
비동기 SMTP 이메일 발송 서비스.
SMTP 미설정 시 경고 로그만 출력하고 서비스를 중단하지 않습니다.
"""
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.config import settings

logger = logging.getLogger("ium.email")

_TEMPLATES: dict[str, dict] = {
    "crisis": {
        "subject": "[긴급] 이음 사용자 위기 상황 감지",
        "body": (
            "<h2>⚠️ 위기 상황 감지</h2>"
            "<p>사용자 <strong>{nickname}</strong>({short_id})의 대화에서 위기 신호가 감지되었습니다.</p>"
            "<p><strong>심각도:</strong> {severity}</p>"
            "<p><strong>감지 시각:</strong> {timestamp}</p>"
            "<p><strong>메모:</strong> {note}</p>"
            "<hr><p>이음 대시보드에서 즉시 확인하고 대응해 주세요.</p>"
        ),
    },
    "no_contact": {
        "subject": "[주의] 이음 사용자 3일 이상 미접속",
        "body": (
            "<h2>📵 미접속 알림</h2>"
            "<p>사용자 <strong>{nickname}</strong>({short_id})이(가) 3일 이상 접속하지 않았습니다.</p>"
            "<p><strong>마지막 접속:</strong> {last_seen}</p>"
            "<hr><p>이음 대시보드에서 안부 확인을 해주세요.</p>"
        ),
    },
    "emotion_drop": {
        "subject": "[주의] 이음 사용자 감정 악화 지속",
        "body": (
            "<h2>😔 감정 악화 알림</h2>"
            "<p>사용자 <strong>{nickname}</strong>({short_id})의 최근 감정이 지속적으로 부정적입니다.</p>"
            "<p><strong>최근 감정 추세:</strong> {trend}</p>"
            "<hr><p>이음 대시보드에서 상담 개입을 고려해 주세요.</p>"
        ),
    },
}


async def send_alert_email(to_email: str, template: str, **kwargs) -> bool:
    if not settings.smtp_host or not settings.smtp_user:
        logger.warning("[Email] SMTP 미설정 — 이메일 발송 생략 (서비스 계속)")
        return False

    tpl = _TEMPLATES.get(template)
    if not tpl:
        logger.error("[Email] 알 수 없는 템플릿: %s", template)
        return False

    kwargs.setdefault("note", "")
    kwargs.setdefault("last_seen", "기록 없음")
    kwargs.setdefault("trend", "")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = tpl["subject"]
    msg["From"] = settings.smtp_user
    msg["To"] = to_email
    msg.attach(MIMEText(tpl["body"].format(**kwargs), "html", "utf-8"))

    try:
        use_tls = settings.smtp_port == 465
        smtp = aiosmtplib.SMTP(
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            use_tls=use_tls,
        )
        await smtp.connect()
        if settings.smtp_port == 587:
            await smtp.starttls()
        await smtp.login(settings.smtp_user, settings.smtp_password)
        await smtp.send_message(msg)
        await smtp.quit()
        logger.info("[Email] 발송 성공: %s (%s)", to_email, template)
        return True
    except Exception as exc:
        logger.warning("[Email] 발송 실패 (서비스 계속): %s", exc)
        return False
