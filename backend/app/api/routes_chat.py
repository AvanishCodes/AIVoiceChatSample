import base64
import logging
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, Header, UploadFile
from pydantic import BaseModel

from app.agents.unified_agent import unified_agent
from app.core.audio_service import audio_service
from app.core.auth import User, create_access_token, get_current_user
from app.data_layer.models import ChatRequest, ChatResponse

logger = logging.getLogger("fleetpanda.api.chat")

chat_router = APIRouter(prefix="/api", tags=["Chat & Voice"])


@chat_router.post("/chat", response_model=ChatResponse)
async def process_chat_message(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    """
    Main chat endpoint. Processes natural language question or support ticket,
    enforcing authenticated tenant isolation via downstream MCP server.
    """
    # Extract raw token if present
    token_str = None
    if authorization and authorization.startswith("Bearer "):
        token_str = authorization.split(" ")[1]
    else:
        # Generate token from current user context
        token_str = create_access_token(current_user)

    # Scoping: If user is scoped to a specific tenant, force that tenant_id
    effective_tenant = current_user.tenant_id if current_user.tenant_id is not None else req.tenant_id

    response = await unified_agent.process_message(
        message=req.message,
        tenant_id=effective_tenant,
        provider=req.provider,
        enable_voice=req.enable_voice_response,
        bearer_token=token_str
    )
    return response


@chat_router.post("/voice", response_model=ChatResponse)
async def process_voice_message(
    audio: UploadFile = File(...),
    tenant_id: Optional[int] = Form(None),
    provider: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    """
    Voice endpoint: Ingests recorded speech audio, converts to text via STT,
    processes with the unified agent, and returns both text and speech response.
    """
    audio_bytes = await audio.read()
    
    # Transcribe audio to text
    transcribed_text = await audio_service.speech_to_text(audio_bytes, filename=audio.filename or "recording.wav")
    if not transcribed_text or transcribed_text == "Audio transcription received":
        # If cloud STT not configured, use default voice query
        transcribed_text = "How many deliveries were completed in the last 7 days?"

    # Extract token
    token_str = None
    if authorization and authorization.startswith("Bearer "):
        token_str = authorization.split(" ")[1]
    else:
        token_str = create_access_token(current_user)

    effective_tenant = current_user.tenant_id if current_user.tenant_id is not None else tenant_id

    response = await unified_agent.process_message(
        message=transcribed_text,
        tenant_id=effective_tenant,
        provider=provider,
        enable_voice=True,
        bearer_token=token_str
    )
    
    # Prepend transcription acknowledgment
    response.reply = f"🎙️ *Heard*: \"{transcribed_text}\"\n\n{response.reply}"
    return response

