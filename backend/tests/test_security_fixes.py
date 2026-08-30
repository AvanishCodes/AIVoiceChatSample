import sqlite3
import pytest
from app.config import settings
from app.core.security import (
    CrossTenantAccessViolation,
    DDLNotAllowedError,
    SecurityViolationError,
    get_readonly_connection,
    validate_and_sanitize_sql,
)


def test_vulnerability_1_prompt_injection_tenant_bypass():
    """
    Vulnerability 1: Attacker attempts prompt injection to bypass tenant filter
    e.g., 'SELECT * FROM customers WHERE tenant_id = 2 --' when authenticated as Tenant 1.
    """
    injected_sql = "SELECT * FROM delivery_orders WHERE tenant_id = 2"
    with pytest.raises(CrossTenantAccessViolation):
        validate_and_sanitize_sql(injected_sql, enforce_tenant_id=1)


def test_vulnerability_2_arbitrary_ddl_dml_execution():
    """
    Vulnerability 2: Attacker attempts destructive DDL/DML (DROP TABLE, DELETE, ATTACH).
    """
    # 1. Blocked at AST validation layer
    with pytest.raises(DDLNotAllowedError):
        validate_and_sanitize_sql("DROP TABLE delivery_orders")

    with pytest.raises(DDLNotAllowedError):
        validate_and_sanitize_sql("ATTACH DATABASE '/tmp/pwn.db' AS pwn")

    # 2. Blocked at SQLite authorizer engine layer even if invoked directly on connection
    conn = get_readonly_connection(settings.DATABASE_PATH)
    cur = conn.cursor()
    with pytest.raises(sqlite3.DatabaseError):
        cur.execute("DELETE FROM customers WHERE customer_id = 1")
    conn.close()


def test_vulnerability_3_unvalidated_input_and_idor(client, tenant1_token):
    """
    Vulnerability 3: Attacker attempts IDOR by providing a different tenant_id in the body.
    The MCP server enforces the verified Bearer token tenant claims over the body parameter.
    """
    resp = client.post(
        "/api/mcp/call",
        headers={"Authorization": f"Bearer {tenant1_token}"},
        json={
            "tool_name": "execute_sql_query",
            "arguments": {
                "sql": "SELECT * FROM customers",
                "tenant_id": 2  # Spoofed body tenant_id
            }
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    # The MCP layer should either reject or force tenant_id = 1 from claims
    if data["success"]:
        assert "tenant_id = 1" in data["result"]["sql"]
    else:
        assert "Cross-tenant access violation" in data["error"] or "Access Denied" in data["error"]

