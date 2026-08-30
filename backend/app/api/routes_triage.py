from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel

from app.agents.triage_agent import triage_agent
from app.core.auth import User, create_access_token, get_current_user
from app.data_layer.data_loader import data_loader
from app.data_layer.models import TicketBrief

triage_router = APIRouter(prefix="/api/triage", tags=["Ticket Triage"])


class TicketTriageRequest(BaseModel):
    ticket_id: Optional[int] = None
    tenant_id: Optional[int] = None
    tenant_name: Optional[str] = None
    subject: str
    description: str
    product_area: Optional[str] = None
    priority: Optional[str] = "medium"
    submitter_email: Optional[str] = None


class SampleTicketScenario(BaseModel):
    scenario_id: str
    title: str
    scenario_type: str  # "low_health_expiring", "duplicate_ticket", "inactive_module"
    description: str
    ticket_data: Dict[str, Any]


SAMPLE_SCENARIOS: List[SampleTicketScenario] = [
    SampleTicketScenario(
        scenario_id="scenario-low-health",
        title="Low-Health Customer with Expiring Contract",
        scenario_type="low_health_expiring",
        description="Desert Sun Petroleum (Health 28/100, CARR $36k) with contract ending on 2026-07-15 submits urgent ticket.",
        ticket_data={
            "ticket_id": 1030,
            "tenant_id": 4,
            "tenant_name": "Desert Sun Petroleum",
            "subject": "Cannot generate monthly invoice batch",
            "description": "Monthly invoice batch generation keeps failing with timeout error. End of month is tomorrow and we need to bill our fuel customers urgently.",
            "product_area": "invoicing",
            "priority": "urgent",
            "submitter_email": "contact_4_0@desertsunpetroleum.com"
        }
    ),
    SampleTicketScenario(
        scenario_id="scenario-duplicate",
        title="Duplicate Ticket Detection",
        scenario_type="duplicate_ticket",
        description="Ticket #1083 referencing previously unresolved ticket #1027 with identical symptoms.",
        ticket_data={
            "ticket_id": 1083,
            "tenant_id": 4,
            "tenant_name": "Desert Sun Petroleum",
            "subject": "TankLink device not sending data since Tuesday",
            "description": "TankLink device not sending data since Tuesday. Please look into this when you get a chance. This is still happening, same issue as ticket #1027.",
            "product_area": "tank_monitor",
            "priority": "high",
            "submitter_email": "contact_4_2@desertsunpetroleum.com"
        }
    ),
    SampleTicketScenario(
        scenario_id="scenario-inactive-module",
        title="Ticket for Inactive / Unpurchased Module",
        scenario_type="inactive_module",
        description="Customer submits issue for 'tank_monitor' module, but their account only has 'dispatch' and 'pricing' active.",
        ticket_data={
            "ticket_id": 1083,
            "tenant_id": 4,
            "tenant_name": "Desert Sun",
            "subject": "Tank readings showing 0% for all customer tanks",
            "description": "Our dispatchers noticed tank readings are showing 0% on customer monitors. Need tank monitor alerting fixed ASAP.",
            "product_area": "tank_monitor",
            "priority": "high",
            "submitter_email": "contact_4_1@desertsunpetroleum.com"
        }
    ),
]


@triage_router.get("/samples", response_model=List[SampleTicketScenario])
async def get_sample_scenarios():
    """Returns the 3 key test ticket scenarios required by the assignment."""
    return SAMPLE_SCENARIOS


@triage_router.post("/ticket", response_model=TicketBrief)
async def triage_ticket_endpoint(
    req: TicketTriageRequest,
    current_user: User = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    """
    Triages a support ticket, aggregating context from all 5 sources to produce
    a comprehensive Ticket Brief with escalation recommendations.
    """
    token_str = None
    if authorization and authorization.startswith("Bearer "):
        token_str = authorization.split(" ")[1]
    else:
        token_str = create_access_token(current_user)

    effective_tenant = current_user.tenant_id if current_user.tenant_id is not None else req.tenant_id

    ticket_dict = req.dict()
    if effective_tenant is not None:
        ticket_dict["tenant_id"] = effective_tenant

    brief = await triage_agent.triage_ticket(ticket_dict, bearer_token=token_str)
    return brief

