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


def test_ast_tenant_auto_injection():
    raw_sql = "SELECT * FROM delivery_orders WHERE status = 'completed'"
    clean_sql, warnings = validate_and_sanitize_sql(raw_sql, enforce_tenant_id=1)
    assert "tenant_id = 1" in clean_sql
    assert len(warnings) > 0


def test_ast_cross_tenant_denial():
    # User is tenant 1, but query asks for tenant 2
    raw_sql = "SELECT * FROM delivery_orders WHERE tenant_id = 2"
    with pytest.raises(CrossTenantAccessViolation):
        validate_and_sanitize_sql(raw_sql, enforce_tenant_id=1)


def test_ast_multi_statement_rejection():
    raw_sql = "SELECT * FROM drivers; SELECT * FROM customers;"
    with pytest.raises(SecurityViolationError):
        validate_and_sanitize_sql(raw_sql)


def test_ast_ddl_dml_rejection():
    # DROP
    with pytest.raises(DDLNotAllowedError):
        validate_and_sanitize_sql("DROP TABLE customers")
    
    # DELETE
    with pytest.raises(DDLNotAllowedError):
        validate_and_sanitize_sql("DELETE FROM delivery_orders WHERE order_id = 1")

    # INSERT
    with pytest.raises(DDLNotAllowedError):
        validate_and_sanitize_sql("INSERT INTO drivers (driver_id, tenant_id, name) VALUES (999, 1, 'Hacker')")


def test_sqlite_readonly_authorizer():
    conn = get_readonly_connection(settings.DATABASE_PATH)
    cur = conn.cursor()

    # Valid SELECT
    cur.execute("SELECT count(*) FROM customers")
    count = cur.fetchone()[0]
    assert count > 0

    # Blocked INSERT at SQLite authorizer level
    with pytest.raises(sqlite3.DatabaseError):
        cur.execute("INSERT INTO customers (customer_id, tenant_id, name) VALUES (9999, 1, 'Injected')")

    # Blocked DROP TABLE
    with pytest.raises(sqlite3.DatabaseError):
        cur.execute("DROP TABLE customers")

    conn.close()


@pytest.mark.asyncio
async def test_agent_cross_tenant_question_refusal():
    from app.agents.sql_agent import sql_agent
    # Scoped user from Tenant 1 asks for Tenant 3 data
    ans, res = await sql_agent.answer_question("Show me the top 5 drivers by total deliveries for tenant 3", tenant_id=1)
    assert res.error is not None
    assert "Access Denied" in ans
    assert "Cross-Tenant" in ans
    assert res.row_count == 0


