import difflib
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.data_layer.data_loader import data_loader
from app.data_layer.entity_resolver import entity_resolver
from app.data_layer.models import (
    CustomerProfile,
    EscalationDetails,
    OperationalSnapshot,
    Ticket,
    TicketBrief,
)
from app.mcp.server import fetch_operational_snapshot

logger = logging.getLogger("fleetpanda.triage_agent")


class TriageAgent:
    """
    Support Ticket Triage Agent:
    Pulls intelligence from all 5 data sources to generate structured ticket briefs
    with intelligent escalation recommendations, duplicate detection, and inactive module alerts.
    """
    def __init__(self):
        pass

    async def triage_ticket(
        self,
        ticket_input: Dict[str, Any],
        bearer_token: Optional[str] = None
    ) -> TicketBrief:
        """
        Processes a ticket and produces a comprehensive Ticket Brief.
        """
        # 1. Resolve Tenant ID
        tenant_id = ticket_input.get("tenant_id")
        tenant_name = ticket_input.get("tenant_name", "")
        submitter_email = ticket_input.get("submitter_email", "")
        subject = ticket_input.get("subject", "")
        description = ticket_input.get("description", "")
        product_area = ticket_input.get("product_area", "")
        ticket_id = ticket_input.get("ticket_id")

        if tenant_id is None:
            # Try resolving from email or name
            resolved = entity_resolver.resolve_tenant(submitter_email or tenant_name or subject)
            if resolved:
                tenant_id = resolved[0]
            else:
                tenant_id = 1  # Default fallback

        # 2. Source 1: Customer Profile
        customer = data_loader.get_customer(tenant_id)
        if not customer:
            customer = CustomerProfile(
                tenant_id=tenant_id,
                name=tenant_name or f"Tenant {tenant_id}",
                health_score=50,
                carr=50000,
                modules_active=["dispatch", "pricing"],
                contract_end_date="2027-01-01",
                assigned_csm="Maria",
                fleet_size=10,
                onboarding_status="live",
                region="Unknown"
            )

        # 3. Source 2: Dispatch Operational Data
        ops_snapshot = fetch_operational_snapshot(tenant_id)

        # 4. Source 3: Past Tickets & Duplicate Detection
        tenant_tickets = data_loader.get_tickets_by_tenant(tenant_id)
        relevant_past_tickets, duplicate_info = self._analyze_past_tickets(
            subject=subject,
            description=description,
            current_ticket_id=ticket_id,
            past_tickets=tenant_tickets
        )

        # 5. Source 4: Call History & Sentiment
        all_names = entity_resolver.get_all_known_names_for_tenant(tenant_id)
        all_names.append(customer.name)
        call_transcripts = data_loader.get_transcripts_by_tenant_id(tenant_id, all_names)
        recent_calls_data = [
            {
                "call_id": c.call_id,
                "date": c.date,
                "topic": c.topic,
                "sentiment": c.sentiment,
                "competitor_mentioned": c.competitor_mentioned,
                "action_items": c.action_items,
                "summary": c.summary
            }
            for c in sorted(call_transcripts, key=lambda x: x.date, reverse=True)[:3]
        ]

        # 6. Source 5: Knowledge Base Article Matching
        kb_articles = self._match_kb_articles(
            subject=subject,
            description=description,
            product_area=product_area
        )

        # 7. Check Inactive Module Misconfiguration
        inactive_module_warning = None
        if product_area and product_area not in ["billing", "integration", "login_access", "reporting"]:
            if product_area not in customer.modules_active:
                inactive_module_warning = (
                    f"⚠️ Inactive Module Warning: Customer submitted a ticket for '{product_area}', "
                    f"but this module is NOT active on their plan (Active: {', '.join(customer.modules_active)}). "
                    f"This may require an upsell or permission configuration."
                )

        # 8. Compute Escalation Score & Recommendation
        escalation = self._compute_escalation(
            customer=customer,
            ops_snapshot=ops_snapshot,
            recent_calls=call_transcripts,
            duplicate_info=duplicate_info,
            inactive_module_warning=inactive_module_warning,
            ticket_priority=ticket_input.get("priority", "medium")
        )

        # 9. Generate Suggested Response Draft
        suggested_response = self._generate_suggested_response(
            customer=customer,
            subject=subject,
            kb_articles=kb_articles,
            inactive_warning=inactive_module_warning,
            duplicate_info=duplicate_info
        )

        # 10. Generate Markdown Summary
        summary_md = self._format_brief_markdown(
            ticket_id=ticket_id,
            customer=customer,
            escalation=escalation,
            inactive_warning=inactive_module_warning,
            duplicate_info=duplicate_info,
            past_tickets=relevant_past_tickets,
            kb_articles=kb_articles,
            recent_calls=recent_calls_data,
            ops_snapshot=ops_snapshot,
            suggested_response=suggested_response
        )

        return TicketBrief(
            ticket_id=ticket_id,
            tenant_id=tenant_id,
            tenant_name=customer.name,
            customer_profile=customer,
            escalation=escalation,
            inactive_module_warning=inactive_module_warning,
            duplicate_detection=duplicate_info,
            relevant_past_tickets=relevant_past_tickets,
            relevant_kb_articles=kb_articles,
            recent_calls=recent_calls_data,
            operational_snapshot=ops_snapshot,
            suggested_response=suggested_response,
            summary_markdown=summary_md
        )

    def _analyze_past_tickets(
        self,
        subject: str,
        description: str,
        current_ticket_id: Optional[int],
        past_tickets: List[Ticket]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Finds relevant past tickets and computes duplicate similarity."""
        combined_text = f"{subject} {description}".lower()
        scored_tickets = []
        is_duplicate = False
        duplicate_of: Optional[int] = None
        max_similarity = 0.0

        for t in past_tickets:
            if current_ticket_id and t.ticket_id == current_ticket_id:
                continue

            past_text = f"{t.subject} {t.description}".lower()
            ratio = difflib.SequenceMatcher(None, combined_text, past_text).ratio()
            
            # Check for explicit mention like "same issue as ticket #1027"
            explicit_ref = False
            if f"#{t.ticket_id}" in combined_text or f"ticket {t.ticket_id}" in combined_text:
                explicit_ref = True
                ratio = max(ratio, 0.95)

            if ratio > max_similarity:
                max_similarity = ratio
                if ratio >= 0.70 or explicit_ref:
                    is_duplicate = True
                    duplicate_of = t.ticket_id

            scored_tickets.append({
                "ticket_id": t.ticket_id,
                "subject": t.subject,
                "status": t.status,
                "priority": t.priority,
                "product_area": t.product_area,
                "created_at": t.created_at,
                "resolution": t.resolution,
                "similarity_score": round(ratio, 2),
                "is_explicit_ref": explicit_ref
            })

        scored_tickets.sort(key=lambda x: (x["is_explicit_ref"], x["similarity_score"]), reverse=True)

        duplicate_info = {
            "is_duplicate": is_duplicate,
            "duplicate_of_ticket_id": duplicate_of,
            "confidence": round(max_similarity, 2),
            "duplicate_note": f"High similarity ({round(max_similarity*100)}%) with prior ticket #{duplicate_of}" if is_duplicate else "No duplicate ticket detected"
        }

        return scored_tickets[:4], duplicate_info

    def _match_kb_articles(
        self,
        subject: str,
        description: str,
        product_area: str
    ) -> List[Dict[str, Any]]:
        """Matches knowledge base articles ranked by symptom keywords and relevance."""
        text = f"{subject} {description}".lower()
        matched = []

        for kb in data_loader.kb_articles:
            score = 0.0
            if product_area and kb.product_area == product_area:
                score += 3.0

            # Match symptoms
            for s in kb.symptoms:
                if s.lower() in text or any(word in text for word in s.lower().split() if len(word) > 4):
                    score += 2.5

            # Match title
            if kb.title.lower() in text:
                score += 4.0

            # Match root cause keywords
            for word in ["login", "cache", "tanklink", "quickbooks", "invoice", "margin", "route", "csv", "portal", "gps", "duplicate", "dashboard"]:
                if word in text and (word in kb.title.lower() or word in kb.root_cause.lower()):
                    score += 1.5

            if score > 0:
                matched.append({
                    "article_id": kb.article_id,
                    "title": kb.title,
                    "product_area": kb.product_area,
                    "root_cause": kb.root_cause,
                    "resolution": kb.resolution,
                    "relevance_score": round(score, 1),
                    "updated_at": kb.updated_at
                })

        matched.sort(key=lambda x: (x["relevance_score"], x["updated_at"]), reverse=True)
        return matched[:3]

    def _compute_escalation(
        self,
        customer: CustomerProfile,
        ops_snapshot: OperationalSnapshot,
        recent_calls: List[Any],
        duplicate_info: Dict[str, Any],
        inactive_module_warning: Optional[str],
        ticket_priority: str
    ) -> EscalationDetails:
        """Computes escalation score and actionable rationale."""
        score = 0
        reasons = []
        action_plan = []

        # 1. Health Score Factor
        if customer.health_score < 40:
            score += 35
            reasons.append(f"Critical Health Score: {customer.health_score}/100 (<40 is severe churn risk).")
            action_plan.append(f"Notify assigned CSM ({customer.assigned_csm}) immediately.")
        elif customer.health_score < 65:
            score += 15
            reasons.append(f"Moderate Health Score: {customer.health_score}/100.")

        # 2. CARR Factor
        if customer.carr >= 75000:
            score += 20
            reasons.append(f"High-Value Account: ${customer.carr:,} CARR.")
        elif customer.carr >= 50000:
            score += 10
            reasons.append(f"Mid-Tier Value Account: ${customer.carr:,} CARR.")

        # 3. Contract Proximity
        if customer.contract_end_date.startswith("2026"):
            score += 25
            reasons.append(f"Imminent Contract Renewal: {customer.contract_end_date} (within 90-180 days).")
            action_plan.append("Coordinate with CSM before sending formal technical resolution.")

        # 4. Inactive Module Misconfiguration
        if inactive_module_warning:
            score += 20
            reasons.append("Inactive Module Issue: Customer is filing tickets for unpurchased/unactivated module.")
            action_plan.append("Explain plan inclusions and initiate expansion/upsell conversation.")

        # 5. Duplicate Ticket Detection
        if duplicate_info.get("is_duplicate"):
            score += 15
            reasons.append(f"Recurring / Duplicate Issue: Linked to ticket #{duplicate_info.get('duplicate_of_ticket_id')}.")
            action_plan.append(f"Review previous resolution on ticket #{duplicate_info.get('duplicate_of_ticket_id')}.")

        # 6. Call Sentiment & Competitors
        for call in recent_calls:
            if getattr(call, "competitor_mentioned", False):
                score += 20
                reasons.append("Competitor Mentioned: Customer actively evaluating alternative vendors in recent calls.")
                action_plan.append("Flag account for urgent executive CSM intervention.")
                break
            if getattr(call, "sentiment", "") == "negative":
                score += 10
                reasons.append("Negative Call Sentiment: Customer recently expressed dissatisfaction.")
                break

        # 7. Operational anomalies
        if ops_snapshot.emergency_orders_count >= 10:
            score += 10
            reasons.append(f"Operational Strain: {ops_snapshot.emergency_orders_count} emergency orders in last 30 days.")

        # Determine level
        churn_risk = customer.health_score < 40 or customer.contract_end_date.startswith("2026")
        if score >= 60:
            level = "CRITICAL"
        elif score >= 40:
            level = "HIGH"
        elif score >= 20:
            level = "MEDIUM"
        else:
            level = "LOW"

        if not action_plan:
            action_plan.append("Resolve ticket using standard support troubleshooting guidelines.")

        return EscalationDetails(
            level=level,
            score=min(100, score),
            churn_risk=churn_risk,
            reasons=reasons,
            action_plan=action_plan
        )

    def _generate_suggested_response(
        self,
        customer: CustomerProfile,
        subject: str,
        kb_articles: List[Dict[str, Any]],
        inactive_warning: Optional[str],
        duplicate_info: Dict[str, Any]
    ) -> str:
        """Generates a professional, context-aware draft response."""
        greeting = f"Hi {customer.name} Team,\n\nThank you for reaching out to FleetPanda Support regarding '{subject}'."

        if inactive_warning:
            body = (
                f"We reviewed your account configuration and noticed that this feature is currently not part of your active modules "
                f"({', '.join(customer.modules_active)}). Your assigned CSM, {customer.assigned_csm}, would be happy to walk you through "
                f"enabling this module for your fleet."
            )
        elif kb_articles:
            top_kb = kb_articles[0]
            body = (
                f"Based on our diagnostics, this issue is typically resolved with the following steps:\n"
                f"• {top_kb['resolution']}\n\n"
                f"Reference Article: {top_kb['article_id']} - {top_kb['title']}"
            )
        else:
            body = (
                f"Our engineering and support team is actively investigating this behavior. "
                f"We have verified your dispatch telemetry and are applying the appropriate diagnostic steps."
            )

        closing = f"\n\nBest regards,\nFleetPanda Support Team (Assigned CSM: {customer.assigned_csm})"
        return f"{greeting}\n\n{body}{closing}"

    def _format_brief_markdown(
        self,
        ticket_id: Optional[int],
        customer: CustomerProfile,
        escalation: EscalationDetails,
        inactive_warning: Optional[str],
        duplicate_info: Dict[str, Any],
        past_tickets: List[Dict[str, Any]],
        kb_articles: List[Dict[str, Any]],
        recent_calls: List[Dict[str, Any]],
        ops_snapshot: OperationalSnapshot,
        suggested_response: str
    ) -> str:
        """Formats the brief as a structured markdown report."""
        tid_str = f"#{ticket_id}" if ticket_id else "Incoming Ticket"
        
        lines = [
            f"# 📋 Ticket Triage Brief: {tid_str} — {customer.name}",
            "",
            f"### 🏢 Customer Profile & Commercial Context",
            f"- **Tenant**: {customer.name} (Tenant ID: {customer.tenant_id}) | **Region**: {customer.region}",
            f"- **Health Score**: **{customer.health_score}/100** | **CARR**: **${customer.carr:,}** | **Fleet Size**: {customer.fleet_size} trucks",
            f"- **Contract End Date**: **{customer.contract_end_date}** | **Assigned CSM**: {customer.assigned_csm}",
            f"- **Active Modules**: `{', '.join(customer.modules_active)}`",
            "",
            f"### 🚨 Escalation Recommendation: **{escalation.level}** (Risk Score: {escalation.score}/100)",
        ]

        for r in escalation.reasons:
            lines.append(f"- ⚠️ {r}")

        lines.append("\n**Action Plan:**")
        for a in escalation.action_plan:
            lines.append(f"- ✅ {a}")

        if inactive_warning:
            lines.extend(["", f"> **{inactive_warning}**"])

        if duplicate_info.get("is_duplicate"):
            lines.extend(["", f"> 🔁 **Duplicate Detection Alert**: {duplicate_info.get('duplicate_note')}"])

        lines.extend([
            "",
            "### 📊 Dispatch Operational Snapshot (Last 30 Days)",
            f"- **Completed Deliveries**: {ops_snapshot.deliveries_last_30d:,} ({ops_snapshot.gallons_last_30d:,.0f} gallons)",
            f"- **Fill Rate**: {ops_snapshot.fill_rate * 100:.1f}% | **Emergency Orders**: {ops_snapshot.emergency_orders_count}",
            f"- **Active Fleet**: {ops_snapshot.active_trucks_count} trucks | {ops_snapshot.active_drivers_count} active drivers",
            "",
            "### 📚 Matched Knowledge Base Articles",
        ])

        if kb_articles:
            for kb in kb_articles:
                lines.append(f"- **[{kb['article_id']}] {kb['title']}** (Relevance: {kb['relevance_score']})")
                lines.append(f"  - *Root Cause*: {kb['root_cause']}")
                lines.append(f"  - *Resolution*: {kb['resolution']}")
        else:
            lines.append("- No specific KB article matched.")

        lines.extend(["", "### 📞 Recent Call Context & Sentiment"])
        if recent_calls:
            for c in recent_calls:
                comp_str = " (⚠️ Competitor Mentioned)" if c.get("competitor_mentioned") else ""
                lines.append(f"- **{c['date']}** — *{c['topic']}* [Sentiment: `{c['sentiment'].upper()}`{comp_str}]")
                lines.append(f"  - Summary: {c['summary']}")
        else:
            lines.append("- No recent calls on record.")

        lines.extend([
            "",
            "### ✉️ Suggested Response Draft",
            "```text",
            suggested_response,
            "```"
        ])

        return "\n".join(lines)


triage_agent = TriageAgent()

