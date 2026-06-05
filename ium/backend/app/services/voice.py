"""
Phase 1: Whisper(STT) + OpenAI TTS
Phase 3 전환: Clova Speech(STT) + Clova Voice(TTS)
설정값(clova_client_id)이 채워지면 자동으로 Clova로 전환.
"""
import io
import httpx
from app.config import settings

# Lazy initialization to allow running without API keys
_openai_client = None

def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        from openai import AsyncOpenAI
        _openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _openai_client

CLOVA_STT_URL = "https://naveropenapi.apigw.ntruss.com/recog/v1/stt"
CLOVA_TTS_URL = "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts"


async def speech_to_text(audio_bytes: bytes) -> str:
    if settings.clova_client_id:
        return await _clova_stt(audio_bytes)
    return await _whisper_stt(audio_bytes)


async def text_to_speech(text: str) -> bytes:
    if settings.clova_client_id:
        return await _clova_tts(text)
    return await _openai_tts(text)


async def _whisper_stt(audio_bytes: bytes) -> str:
    audio_file = ("audio.webm", io.BytesIO(audio_bytes), "audio/webm")
    client = _get_openai_client()
    transcript = await client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="ko",
    )
    return transcript.text


async def _openai_tts(text: str) -> bytes:
    client = _get_openai_client()
    response = await client.audio.speech.create(
        model="tts-1",
        voice="nova",   # 차분한 여성 목소리
        input=text,
        speed=0.9,      # 노인용: 약간 느리게
    )
    return response.content


async def _clova_stt(audio_bytes: bytes) -> str:
    headers = {
        "X-NCP-APIGW-API-KEY-ID": settings.clova_client_id,
        "X-NCP-APIGW-API-KEY": settings.clova_client_secret,
        "Content-Type": "application/octet-stream",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            CLOVA_STT_URL,
            headers=headers,
            params={"lang": "Kor"},
            content=audio_bytes,
        )
        resp.raise_for_status()
        return resp.json().get("text", "")


async def _clova_tts(text: str) -> bytes:
    headers = {
        "X-NCP-APIGW-API-KEY-ID": settings.clova_client_id,
        "X-NCP-APIGW-API-KEY": settings.clova_client_secret,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "speaker": "nmijin",
        "volume": "0",
        "speed": "-2",  # 노인용: 느리게
        "pitch": "0",
        "text": text,
        "format": "mp3",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(CLOVA_TTS_URL, headers=headers, data=data)
        resp.raise_for_status()
        return resp.content
