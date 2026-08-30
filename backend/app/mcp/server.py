import logging
import sqlite3
import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.config import settings
from app.core.auth import decode_token
from app.core.security import (
    CrossTenantAccessViolation,
    DDLNotAllowedError,
    SecurityViolationError,
    get_readonly_connection,
    validate_and_sanitize_sql,
)
from app.data_layer.data_loader import data_loader
from app.data_layer.entity_resolver import entity_resolver
from app.data_layer.models import OperationalSnapshot, SqlQueryResult

logger = logging.getLogger("fleetpanda.mcp")

mcp_router = APIRouter(prefix="/api/mcp", tags=["Model Context Protocol (MCP)"])


class McpToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]


class McpCallRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class McpCallResponse(BaseModel):
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time_ms: float = 0.0


# Tool Definitions Catalog
MCP_TOOLS: List[McpToolDefinition] = [
    McpToolDefinition(
        name="execute_sql_query",
        description="Executes a sanitized, read-only SELECT query on the dispatch SQLite database with deterministic multi-tenant isolation.",
        input_schema={
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "The SQLite SELECT query to execute"},
                "tenant_id": {"type": "integer", "description": "Optional target tenant ID (enforced for scoped users)"},
            },
            "required": ["sql"],
        },
    ),
    McpToolDefinition(
        name="get_customer_context",
        description="Retrieves the full profile, active modules, and dispatch operational snapshot for a specific tenant.",
        input_schema={
            "type": "object",
            "properties": {
                "tenant_id": {"type": "integer", "description": "Tenant ID to fetch context for"},
            },
            "required": ["tenant_id"],
        },
    ),
    McpToolDefinition(
        name="search_knowledge_base",
        description="Searches the 12 known-issue knowledge base articles by symptom keywords or product area.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query or symptoms"},
                "product_area": {"type": "string", "description": "Optional product area filter"},
            },
            "required": ["query"],
        },
    ),
    McpToolDefinition(
        name="resolve_tenant_entity",
        description="Resolves informal company names, aliases, acronyms, and email domains to canonical tenant_id.",
        input_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Company name, alias, or email domain"},
            },
            "required": ["name"],
        },
    ),
]


def extract_and_verify_token(authorization: Optional[str]) -> Dict[str, Any]:
    """Extracts and verifies Bearer token claims for MCP requests."""
    if not authorization:
        # Default fallback to CSM claims in dev mode
        return {
            "sub": "usr-csm-01",
            "role": "csm",
            "tenant_id": None,
            "permissions": ["read", "query_sql", "triage_tickets", "cross_tenant"],
        }
    
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'",
        )
    
    token = parts[1]
    return decode_token(token)


@mcp_router.get("/tools", response_model=List[McpToolDefinition])
async def list_mcp_tools(authorization: Optional[str] = Header(None)):
    """List available MCP tools for the authenticated user."""
    _ = extract_and_verify_token(authorization)
    return MCP_TOOLS


@mcp_router.post("/call", response_model=McpCallResponse)
async def call_mcp_tool(
    request: McpCallRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Executes an MCP tool with Bearer token authentication and tenant data segregation.
    """
    start_time = time.time()
    claims = extract_and_verify_token(authorization)
    scoped_tenant_id = claims.get("tenant_id")
    role = claims.get("role", "user")
    allow_cross_tenant = "cross_tenant" in claims.get("permissions", []) or scoped_tenant_id is None

    tool_name = request.tool_name
    args = request.arguments

    try:
        if tool_name == "execute_sql_query":
            raw_sql = args.get("sql", "")
            target_tenant = args.get("tenant_id")

            # If user is scoped to a specific tenant, force tenant scoping
            effective_tenant = scoped_tenant_id if scoped_tenant_id is not None else target_tenant

            # 1. AST Validation & Isolation enforcement
            clean_sql, warnings = validate_and_sanitize_sql(
                raw_sql,
                enforce_tenant_id=effective_tenant,
                allow_cross_tenant=allow_cross_tenant and target_tenant is None
            )

            # 2. Execute on hardened read-only SQLite connection
            conn = get_readonly_connection(settings.DATABASE_PATH)
            try:
                cursor = conn.cursor()
                cursor.execute(clean_sql)
                rows = cursor.fetchall()
                cols = [desc[0] for desc in cursor.description] if cursor.description else []
                results = [dict(zip(cols, row)) for row in rows]
            finally:
                conn.close()

            exec_time = (time.time() - start_time) * 1000.0
            sql_res = SqlQueryResult(
                sql=clean_sql,
                explanation=f"Executed securely in read-only mode with tenant isolation ({len(results)} rows returned).",
                results=results,
                row_count=len(results),
                columns=cols,
                execution_time_ms=round(exec_time, 2),
                tenant_id=effective_tenant,
                warnings=warnings
            )
            return McpCallResponse(
                success=True,
                result=sql_res.model_dump(),
                execution_time_ms=round(exec_time, 2)
            )

        elif tool_name == "get_customer_context":
            req_tenant_id = args.get("tenant_id")
            if scoped_tenant_id is not None and req_tenant_id != scoped_tenant_id:
                raise CrossTenantAccessViolation(
                    f"Access Denied: Session restricted to Tenant {scoped_tenant_id}"
                )

            cust = data_loader.get_customer(req_tenant_id)
            if not cust:
                return McpCallResponse(
                    success=False,
                    result=None,
                    error=f"Customer profile not found for Tenant ID {req_tenant_id}",
                    execution_time_ms=(time.time() - start_time) * 1000.0
                )

            # Pull live dispatch operational metrics
            ops_snapshot = fetch_operational_snapshot(req_tenant_id)

            return McpCallResponse(
                success=True,
                result={
                    "customer_profile": cust.model_dump(),
                    "operational_snapshot": ops_snapshot.model_dump()
                },
                execution_time_ms=(time.time() - start_time) * 1000.0
            )

        elif tool_name == "search_knowledge_base":
            query_str = args.get("query", "").lower()
            product_area = args.get("product_area")
            
            matched = []
            for article in data_loader.kb_articles:
                if product_area and article.product_area != product_area:
                    continue
                score = 0
                if query_str:
                    if query_str in article.title.lower():
                        score += 3
                    if any(query_str in s.lower() for s in article.symptoms):
                        score += 2
                    if query_str in article.root_cause.lower() or query_str in article.resolution.lower():
                        score += 1
                matched.append((score, article.model_dump()))
            
            matched.sort(key=lambda x: x[0], reverse=True)
            return McpCallResponse(
                success=True,
                result=[item[1] for item in matched[:5]],
                execution_time_ms=(time.time() - start_time) * 1000.0
            )

        elif tool_name == "resolve_tenant_entity":
            name = args.get("name", "")
            res = entity_resolver.resolve_tenant(name)
            return McpCallResponse(
                success=True,
                result={
                    "resolved": res is not None,
                    "tenant_id": res[0] if res else None,
                    "canonical_name": res[1] if res else None,
                    "confidence": res[2] if res else 0.0
                },
                execution_time_ms=(time.time() - start_time) * 1000.0
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MCP Tool '{tool_name}' not found",
            )

    except (CrossTenantAccessViolation, DDLNotAllowedError, SecurityViolationError) as sec_err:
        return McpCallResponse(
            success=False,
            result=None,
            error=str(sec_err),
            execution_time_ms=(time.time() - start_time) * 1000.0
        )
    except Exception as exc:
        logger.error(f"Error executing MCP tool '{tool_name}': {exc}", exc_info=True)
        return McpCallResponse(
            success=False,
            result=None,
            error=str(exc),
            execution_time_ms=(time.time() - start_time) * 1000.0
        )


def fetch_operational_snapshot(tenant_id: int) -> OperationalSnapshot:
    """Helper to fetch 30-day operational statistics for a tenant from SQLite."""
    conn = get_readonly_connection(settings.DATABASE_PATH)
    try:
        cur = conn.cursor()
        
        # Deliveries, Gallons, Fill rate in last 30d
        cur.execute("""
            WITH max_d AS (SELECT max(delivery_date) as max_date FROM delivery_orders WHERE tenant_id = ?)
            SELECT 
                count(*) as total_deliveries,
                coalesce(sum(gallons_delivered), 0) as total_gallons,
                coalesce(sum(gallons_delivered) * 1.0 / nullif(sum(gallons_ordered), 0), 0) as fill_rate
            FROM delivery_orders, max_d
            WHERE tenant_id = ? 
              AND status = 'completed'
              AND delivery_date >= date(max_d.max_date, '-30 days')
        """, (tenant_id, tenant_id))
        deliv_row = cur.fetchone()
        
        # Emergency orders count
        cur.execute("""
            WITH max_d AS (SELECT max(order_date) as max_date FROM delivery_orders WHERE tenant_id = ?)
            SELECT count(*) 
            FROM delivery_orders, max_d
            WHERE tenant_id = ? 
              AND priority = 'emergency'
              AND order_date >= date(max_d.max_date, '-30 days')
        """, (tenant_id, tenant_id))
        emerg_row = cur.fetchone()
        
        # Active drivers
        cur.execute("SELECT count(*) FROM drivers WHERE tenant_id = ? AND status = 'active'", (tenant_id,))
        drivers_count = cur.fetchone()[0]
        
        # Active trucks
        cur.execute("SELECT count(*) FROM trucks WHERE tenant_id = ? AND status = 'operational'", (tenant_id,))
        trucks_count = cur.fetchone()[0]
        
        # Critical tanks (level < 20%)
        cur.execute("""
            SELECT count(*) FROM tank_readings 
            WHERE tenant_id = ? AND level_percent < 20.0
        """, (tenant_id,))
        tanks_count = cur.fetchone()[0]

        return OperationalSnapshot(
            deliveries_last_30d=deliv_row["total_deliveries"] if deliv_row else 0,
            gallons_last_30d=round(deliv_row["total_gallons"], 2) if deliv_row else 0.0,
            fill_rate=round(deliv_row["fill_rate"], 3) if deliv_row else 0.0,
            emergency_orders_count=emerg_row[0] if emerg_row else 0,
            active_drivers_count=drivers_count,
            active_trucks_count=trucks_count,
            critical_tanks_count=tanks_count
        )
    finally:
        conn.close()
