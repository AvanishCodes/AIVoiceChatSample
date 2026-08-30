from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel

from app.agents.sql_agent import sql_agent
from app.core.auth import User, create_access_token, get_current_user
from app.data_layer.models import SqlQueryResult

sql_router = APIRouter(prefix="/api/sql", tags=["Dispatch SQL"])


class SqlQueryRequest(BaseModel):
    query: str
    tenant_id: Optional[int] = None
    provider: Optional[str] = None


class BenchmarkItem(BaseModel):
    id: int
    question: str
    category: str
    expected_focus: str


BENCHMARK_QUESTIONS: List[BenchmarkItem] = [
    BenchmarkItem(
        id=1,
        question="How many deliveries were completed in the last 7 days across all tenants?",
        category="Global Volume",
        expected_focus="Filtered by status='completed' and delivery_date within 7 days of dataset max date."
    ),
    BenchmarkItem(
        id=2,
        question="Which tenant delivered the most gallons of diesel last month?",
        category="Product Aggregation",
        expected_focus="Aggregates gallons_delivered for diesel orders in previous operational month (April 2026)."
    ),
    BenchmarkItem(
        id=3,
        question="Show me the top 5 drivers by total deliveries for tenant 3",
        category="Driver Performance",
        expected_focus="Scoped strictly to tenant_id=3, joins drivers and delivery_orders."
    ),
    BenchmarkItem(
        id=4,
        question="What is the average gallons per delivery for propane orders?",
        category="Product Metrics",
        expected_focus="Calculates avg(gallons_delivered) across completed propane deliveries."
    ),
    BenchmarkItem(
        id=5,
        question="How many emergency orders did tenant 4 have in the past 30 days?",
        category="Priority & Anomaly",
        expected_focus="Scoped strictly to tenant_id=4 and priority='emergency' in last 30 days."
    ),
    BenchmarkItem(
        id=6,
        question="Which trucks are currently in maintenance status?",
        category="Fleet Telemetry",
        expected_focus="Filters trucks where status='maintenance'."
    ),
    BenchmarkItem(
        id=7,
        question="What is the fill rate (gallons delivered / gallons ordered) for completed orders by tenant?",
        category="Operational Efficiency",
        expected_focus="Computes sum(gallons_delivered)/sum(gallons_ordered) grouped by tenant."
    ),
    BenchmarkItem(
        id=8,
        question="List tenants with declining delivery volume (compare last 30 days vs previous 30 days)",
        category="Trend Analysis",
        expected_focus="Compares completed delivery counts between [T-30, T] and [T-60, T-30]."
    ),
]


@sql_router.get("/benchmark", response_model=List[BenchmarkItem])
async def get_sql_benchmarks():
    """Returns the 8 standard dispatch SQL benchmark questions."""
    return BENCHMARK_QUESTIONS


@sql_router.post("/query", response_model=SqlQueryResult)
async def query_dispatch_sql(
    req: SqlQueryRequest,
    current_user: User = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    """
    Executes natural language SQL or raw query through the Text-to-SQL Agent and MCP layer.
    """
    token_str = None
    if authorization and authorization.startswith("Bearer "):
        token_str = authorization.split(" ")[1]
    else:
        token_str = create_access_token(current_user)

    effective_tenant = current_user.tenant_id if current_user.tenant_id is not None else req.tenant_id

    _, sql_res = await sql_agent.answer_question(
        question=req.query,
        tenant_id=effective_tenant,
        provider=req.provider,
        bearer_token=token_str
    )
    return sql_res

