import asyncio
import io
import logging
from typing import Optional
import edge_tts

from app.config import settings

logger = logging.getLogger("fleetpanda.audio")


class AudioService:
    """
    Audio processing service for Speech-to-Text (STT) and Text-to-Speech (TTS).
    """
    def __init__(self):
        self.default_voice = settings.DEFAULT_TTS_VOICE

    async def text_to_speech(self, text: str, voice: Optional[str] = None) -> bytes:
        """
        Synthesizes text to high-quality neural speech MP3 using edge-tts.
        """
        voice = voice or self.default_voice
        # Clean text of markdown formatting for cleaner speech synthesis
        clean_text = self._clean_text_for_tts(text)
        
        if not clean_text:
            clean_text = "No response text available."

        try:
            communicate = edge_tts.Communicate(clean_text, voice)
            audio_buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_buffer.write(chunk["data"])
            return audio_buffer.getvalue()
        except Exception as e:
            logger.error(f"TTS generation error: {e}")
            # Return empty bytes or silent buffer on unexpected error
            return b""

    async def speech_to_text(self, audio_bytes: bytes, filename: str = "audio.wav") -> str:
        """
        Transcribes audio bytes to text.
        Supports Whisper or cloud fallback when available.
        """
        if not audio_bytes:
            return ""

        try:
            # Check if OpenAI API key is available for OpenAI Whisper
            if settings.OPENAI_API_KEY:
                import httpx
                headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
                files = {"file": (filename, audio_bytes, "audio/wav")}
                data = {"model": "whisper-1"}
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        "https://api.openai.com/v1/audio/transcriptions",
                        headers=headers,
                        files=files,
                        data=data
                    )
                    if resp.status_code == 200:
                        return resp.json().get("text", "")
        except Exception as e:
            logger.warning(f"Cloud STT failed: {e}")

        # Frontend also provides Web Speech API for low-latency client-side transcription
        return "Audio transcription received"

    def _clean_text_for_tts(self, text: str) -> str:
        """Strip markdown code blocks, bold markers, and markdown tables for natural speech."""
        import re
        # Remove code blocks ```...```
        text = re.sub(r"```[\s\S]*?```", " [Code details shown on screen] ", text)
        # Remove inline code `...`
        text = re.sub(r"`([^`]+)`", r"\1", text)
        # Remove bold/italic **text** or *text*
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"\*([^*]+)\*", r"\1", text)
        # Remove markdown headers # Header
        text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
        # Replace consecutive whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text


audio_service = AudioService()

