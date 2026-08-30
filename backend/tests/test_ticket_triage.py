import pytest
from app.agents.triage_agent import triage_agent


@pytest.mark.asyncio
async def test_triage_low_health_expiring_contract():
    ticket_input = {
        "ticket_id": 1030,
        "tenant_id": 4,
        "tenant_name": "Desert Sun Petroleum",
        "subject": "Cannot generate monthly invoice batch",
        "description": "Monthly invoice batch generation keeps failing with timeout error. End of month is tomorrow.",
        "product_area": "invoicing",
        "priority": "urgent",
        "submitter_email": "contact_4_0@desertsunpetroleum.com"
    }

    brief = await triage_agent.triage_ticket(ticket_input)
    assert brief.tenant_id == 4
    assert brief.customer_profile.health_score == 28
    assert brief.customer_profile.contract_end_date == "2026-07-15"
    assert brief.escalation.churn_risk is True
    assert brief.escalation.level in ("CRITICAL", "HIGH")
    assert len(brief.escalation.reasons) > 0
    assert "Arcadio" in brief.customer_profile.assigned_csm


@pytest.mark.asyncio
async def test_triage_duplicate_ticket_detection():
    ticket_input = {
        "ticket_id": 1083,
        "tenant_id": 4,
        "tenant_name": "Desert Sun Petroleum",
        "subject": "TankLink device not sending data since Tuesday",
        "description": "TankLink device not sending data since Tuesday. Please look into this. Same issue as ticket #1027",
        "product_area": "tank_monitor",
        "priority": "high",
        "submitter_email": "contact_4_2@desertsunpetroleum.com"
    }

    brief = await triage_agent.triage_ticket(ticket_input)
    assert brief.duplicate_detection["is_duplicate"] is True
    assert brief.duplicate_detection["duplicate_of_ticket_id"] == 1027
    assert brief.duplicate_detection["confidence"] >= 0.70


@pytest.mark.asyncio
async def test_triage_inactive_module_warning():
    ticket_input = {
        "ticket_id": 1099,
        "tenant_id": 4,
        "tenant_name": "Desert Sun Petroleum",
        "subject": "Tank monitor alert thresholds not working",
        "description": "We are trying to configure tank monitor alerts but nothing is firing.",
        "product_area": "tank_monitor",
        "priority": "medium",
        "submitter_email": "contact_4_1@desertsunpetroleum.com"
    }

    brief = await triage_agent.triage_ticket(ticket_input)
    # Desert Sun Petroleum only has ['dispatch', 'pricing'] active
    assert "tank_monitor" not in brief.customer_profile.modules_active
    assert brief.inactive_module_warning is not None
    assert "Inactive Module Warning" in brief.inactive_module_warning

