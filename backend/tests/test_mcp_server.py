import pytest


def test_list_mcp_tools(client, csm_token):
    resp = client.get("/api/mcp/tools", headers={"Authorization": f"Bearer {csm_token}"})
    assert resp.status_code == 200
    tools = resp.json()
    tool_names = [t["name"] for t in tools]
    assert "execute_sql_query" in tool_names
    assert "get_customer_context" in tool_names
    assert "search_knowledge_base" in tool_names
    assert "resolve_tenant_entity" in tool_names


def test_mcp_execute_sql_scoped(client, tenant1_token):
    # Valid query for Tenant 1
    resp = client.post(
        "/api/mcp/call",
        headers={"Authorization": f"Bearer {tenant1_token}"},
        json={
            "tool_name": "execute_sql_query",
            "arguments": {
                "sql": "SELECT count(*) as cnt FROM delivery_orders WHERE status = 'completed'"
            }
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["result"]["row_count"] >= 1
    # Check that query was auto-scoped to tenant_id = 1
    assert "tenant_id = 1" in data["result"]["sql"]


def test_mcp_cross_tenant_rejection(client, tenant1_token):
    # Tenant 1 user attempting to query Tenant 2 data explicitly
    resp = client.post(
        "/api/mcp/call",
        headers={"Authorization": f"Bearer {tenant1_token}"},
        json={
            "tool_name": "execute_sql_query",
            "arguments": {
                "sql": "SELECT * FROM delivery_orders WHERE tenant_id = 2"
            }
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert "Cross-tenant access violation" in data["error"]


def test_mcp_ddl_dml_rejection(client, csm_token):
    # Attempting DROP TABLE
    drop_resp = client.post(
        "/api/mcp/call",
        headers={"Authorization": f"Bearer {csm_token}"},
        json={
            "tool_name": "execute_sql_query",
            "arguments": {
                "sql": "DROP TABLE delivery_orders;"
            }
        }
    )
    assert drop_resp.status_code == 200
    assert drop_resp.json()["success"] is False
    assert "Only read-only SELECT queries are permitted" in drop_resp.json()["error"]

    # Attempting DELETE FROM
    delete_resp = client.post(
        "/api/mcp/call",
        headers={"Authorization": f"Bearer {csm_token}"},
        json={
            "tool_name": "execute_sql_query",
            "arguments": {
                "sql": "DELETE FROM customers WHERE customer_id = 1;"
            }
        }
    )
    assert delete_resp.status_code == 200
    assert delete_resp.json()["success"] is False

