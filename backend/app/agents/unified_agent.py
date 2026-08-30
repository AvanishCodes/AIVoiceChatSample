import base64
import logging
import time
from typing import Any, Dict, Optional

from app.agents.sql_agent import sql_agent
from app.agents.triage_agent import triage_agent
from app.core.audio_service import audio_service
from app.data_layer.entity_resolver import entity_resolver
from app.data_layer.models import ChatResponse

logger = logging.getLogger("fleetpanda.unified_agent")


class UnifiedAgent:
    """
    Unified Orchestrator for FleetPanda Support Agent.
    Routes user input to SQL Agent or Triage Agent, and handles text/audio synthesis.
    """
    def __init__(self):
        pass

    async def process_message(
        self,
        message: str,
        tenant_id: Optional[int] = None,
        provider: Optional[str] = None,
        enable_voice: bool = False,
        bearer_token: Optional[str] = None,
    ) -> ChatResponse:
        start_time = time.time()
        msg_str = message.strip()
        msg_lower = msg_str.lower()

        # Resolve tenant if present in text
        resolved_tenant_id = tenant_id
        if resolved_tenant_id is None:
            resolved = entity_resolver.resolve_tenant(msg_str)
            if resolved:
                resolved_tenant_id = resolved[0]

        # 1. Classify Intent
        # Ticket Triage Intent
        if (
            "triage" in msg_lower
            or "ticket" in msg_lower
            or "issue:" in msg_lower
            or "error:" in msg_lower
            or "quickbooks sync" in msg_lower
            or "tanklink device" in msg_lower
            or "credit memo" in msg_lower
            or "login failure" in msg_lower
            or "submitter:" in msg_lower
        ):
            intent = "ticket_triage"
            ticket_input = {
                "subject": msg_str[:80],
                "description": msg_str,
                "tenant_id": resolved_tenant_id,
                "product_area": self._extract_product_area(msg_lower),
                "priority": "high" if "urgent" in msg_lower or "emergency" in msg_lower else "medium"
            }
            brief = await triage_agent.triage_ticket(ticket_input, bearer_token=bearer_token)
            reply = (
                f"Generated Support Ticket Brief for **{brief.tenant_name}**.\n\n"
                f"🚨 **Escalation Level**: {brief.escalation.level} (Risk Score: {brief.escalation.score}/100)\n"
                f"🏢 **Customer Health**: {brief.customer_profile.health_score}/100 | **CARR**: ${brief.customer_profile.carr:,} | **Assigned CSM**: {brief.customer_profile.assigned_csm}\n\n"
                f"{brief.summary_markdown}"
            )
            sql_res = None
            ticket_brief_res = brief

        # Dispatch Query Intent (Text-to-SQL)
        elif (
            "deliveries" in msg_lower
            or "delivery" in msg_lower
            or "driver" in msg_lower
            or "truck" in msg_lower
            or "gallon" in msg_lower
            or "fill rate" in msg_lower
            or "emergency" in msg_lower
            or "tank reading" in msg_lower
            or "diesel" in msg_lower
            or "propane" in msg_lower
            or "gasoline" in msg_lower
            or "how many" in msg_lower
            or "which tenant" in msg_lower
            or "top 5" in msg_lower
            or "maintenance" in msg_lower
            or "select " in msg_lower
        ):
            intent = "dispatch_query"
            summary, sql_res = await sql_agent.answer_question(
                question=msg_str,
                tenant_id=resolved_tenant_id,
                provider=provider,
                bearer_token=bearer_token
            )
            reply = summary
            ticket_brief_res = None

        # General Conversational Intent
        else:
            intent = "general"
            reply = (
                "Hello! I am FleetPanda's AI Voice & Chat Support Agent.\n\n"
                "I can assist you with:\n"
                "1. **Dispatch Database Queries** (e.g. *'How many deliveries were completed in the last 7 days?'*, *'Show top 5 drivers for tenant 3'*, *'Which trucks are in maintenance?'*)\n"
                "2. **Support Ticket Triage** (e.g. Paste a ticket description to get an automated 5-source brief with health risk analysis, duplicate detection, and suggested response drafts).\n\n"
                "How can I help you today?"
            )
            sql_res = None
            ticket_brief_res = None

        # 2. Voice Synthesis
        audio_b64 = None
        if enable_voice and reply:
            try:
                # Synthesize concise audio
                speech_text = reply.split("\n\n")[0] if len(reply) > 300 else reply
                audio_bytes = await audio_service.text_to_speech(speech_text)
                if audio_bytes:
                    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
            except Exception as e:
                logger.warning(f"Voice synthesis skipped: {e}")

        exec_time = (time.time() - start_time) * 1000.0

        return ChatResponse(
            reply=reply,
            intent=intent,
            sql_result=sql_res,
            ticket_brief=ticket_brief_res,
            audio_base64=audio_b64,
            resolved_tenant_id=resolved_tenant_id,
            execution_time_ms=round(exec_time, 2)
        )

    def _extract_product_area(self, text: str) -> str:
        """Heuristic product area classifier."""
        if "tanklink" in text or "tank reading" in text or "tank" in text:
            return "tank_monitor"
        if "quickbooks" in text or "qbo" in text or "sync" in text:
            return "integration"
        if "invoice" in text or "billing" in text or "credit memo" in text:
            return "invoicing"
        if "login" in text or "password" in text or "credentials" in text or "sso" in text:
            return "login_access"
        if "route" in text or "optimization" in text:
            return "route_builder"
        if "margin" in text or "price" in text or "pricing" in text:
            return "pricing"
        if "dashboard" in text or "report" in text or "analytics" in text:
            return "reporting"
        if "gps" in text or "location" in text:
            return "integration"
        return "dispatch"


unified_agent = UnifiedAgent()

