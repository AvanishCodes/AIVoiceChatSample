from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CustomerProfile(BaseModel):
    tenant_id: int
    name: str
    health_score: int
    carr: int
    modules_active: List[str]
    contract_end_date: str
    assigned_csm: str
    fleet_size: int
    onboarding_status: str
    region: str


class TenantAlias(BaseModel):
    alias: str
    canonical_name: str
    tenant_id: int


class Ticket(BaseModel):
    ticket_id: int
    tenant_id: int
    tenant_name: str
    subject: str
    description: str
    product_area: str
    status: str
    priority: str
    submitter_name: str
    submitter_email: str
    created_at: str
    updated_at: str
    resolution: Optional[str] = None
    agent_name: Optional[str] = None


class CallTranscript(BaseModel):
    call_id: str
    tenant_name: str
    resolved_tenant_id: Optional[int] = None
    participants: List[str]
    topic: str
    summary: str
    sentiment: str  # "positive", "neutral", "negative"
    action_items: List[str]
    date: str
    duration_minutes: int
    competitor_mentioned: bool


class KnowledgeBaseArticle(BaseModel):
    article_id: str
    title: str
    product_area: str
    symptoms: List[str]
    root_cause: str
    resolution: str
    created_at: str
    updated_at: str


class OperationalSnapshot(BaseModel):
    deliveries_last_30d: int = 0
    gallons_last_30d: float = 0.0
    fill_rate: float = 0.0
    emergency_orders_count: int = 0
    active_drivers_count: int = 0
    active_trucks_count: int = 0
    critical_tanks_count: int = 0


class EscalationDetails(BaseModel):
    level: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    score: int  # 0 to 100
    churn_risk: bool
    reasons: List[str]
    action_plan: List[str]


class TicketBrief(BaseModel):
    ticket_id: Optional[int] = None
    tenant_id: int
    tenant_name: str
    customer_profile: CustomerProfile
    escalation: EscalationDetails
    inactive_module_warning: Optional[str] = None
    duplicate_detection: Dict[str, Any] = Field(default_factory=dict)
    relevant_past_tickets: List[Dict[str, Any]] = Field(default_factory=list)
    relevant_kb_articles: List[Dict[str, Any]] = Field(default_factory=list)
    recent_calls: List[Dict[str, Any]] = Field(default_factory=list)
    operational_snapshot: OperationalSnapshot
    suggested_response: str
    summary_markdown: str


class SqlQueryResult(BaseModel):
    sql: str
    explanation: str
    results: List[Dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    columns: List[str] = Field(default_factory=list)
    execution_time_ms: float = 0.0
    tenant_id: Optional[int] = None
    warnings: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class ChatMessage(BaseModel):
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: Optional[str] = None
    sql_result: Optional[SqlQueryResult] = None
    ticket_brief: Optional[TicketBrief] = None
    audio_base64: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    tenant_id: Optional[int] = None
    provider: Optional[str] = None
    enable_voice_response: bool = False


class ChatResponse(BaseModel):
    reply: str
    intent: str  # "dispatch_query", "ticket_triage", "general"
    sql_result: Optional[SqlQueryResult] = None
    ticket_brief: Optional[TicketBrief] = None
    audio_base64: Optional[str] = None
    resolved_tenant_id: Optional[int] = None
    execution_time_ms: float = 0.0

