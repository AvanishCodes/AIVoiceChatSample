import base64
import logging
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel

from app.core.audio_service import audio_service

logger = logging.getLogger("fleetpanda.api.audio")

audio_router = APIRouter(prefix="/api/audio", tags=["Audio & Speech"])


class SynthesizeRequest(BaseModel):
    text: str
    voice: Optional[str] = None


class TranscribeResponse(BaseModel):
    text: str
    confidence: float = 1.0


@audio_router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio_file(audio: UploadFile = File(...)):
    """Transcribes an uploaded audio recording to text."""
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file submitted")

    transcription = await audio_service.speech_to_text(audio_bytes, filename=audio.filename or "recording.wav")
    return TranscribeResponse(text=transcription, confidence=0.98)


@audio_router.post("/synthesize")
async def synthesize_text_to_audio(req: SynthesizeRequest):
    """Synthesizes text into high-quality neural speech MP3 audio stream."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    audio_bytes = await audio_service.text_to_speech(req.text, voice=req.voice)
    if not audio_bytes:
        raise HTTPException(status_code=500, detail="Failed to synthesize speech")

    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline; filename=speech.mp3"}
    )

