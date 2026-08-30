import pytest
from app.agents.sql_agent import sql_agent


@pytest.mark.asyncio
async def test_benchmark_q1_last_7_days():
    q = "How many deliveries were completed in the last 7 days across all tenants?"
    ans, res = await sql_agent.answer_question(q)
    assert res.error is None
    assert res.row_count == 1
    assert "completed_deliveries" in res.results[0]
    count = res.results[0]["completed_deliveries"]
    assert count > 0
    assert "deliveries" in ans


@pytest.mark.asyncio
async def test_benchmark_q2_diesel_last_month():
    q = "Which tenant delivered the most gallons of diesel last month?"
    ans, res = await sql_agent.answer_question(q)
    assert res.error is None
    assert res.row_count == 1
    assert "tenant_id" in res.results[0]
    assert "total_diesel_gallons" in res.results[0]
    assert res.results[0]["tenant_id"] == 3  # Summit Energy Group delivered the most diesel in 2026-04


@pytest.mark.asyncio
async def test_benchmark_q3_top_5_drivers_tenant_3():
    q = "Show me the top 5 drivers by total deliveries for tenant 3"
    ans, res = await sql_agent.answer_question(q, tenant_id=3)
    assert res.error is None
    assert res.row_count == 5
    assert "name" in res.results[0]
    assert "total_deliveries" in res.results[0]


@pytest.mark.asyncio
async def test_benchmark_q4_avg_propane_gallons():
    q = "What is the average gallons per delivery for propane orders?"
    ans, res = await sql_agent.answer_question(q)
    assert res.error is None
    assert res.row_count == 1
    avg_g = res.results[0]["avg_propane_gallons"]
    assert avg_g > 1000  # Expected ~1467.7 gallons


@pytest.mark.asyncio
async def test_benchmark_q5_emergency_orders_tenant_4():
    q = "How many emergency orders did tenant 4 have in the past 30 days?"
    ans, res = await sql_agent.answer_question(q, tenant_id=4)
    assert res.error is None
    assert res.row_count == 1
    cnt = res.results[0]["emergency_orders_count"]
    assert cnt > 0  # Expected 17


@pytest.mark.asyncio
async def test_benchmark_q6_trucks_in_maintenance():
    q = "Which trucks are currently in maintenance status?"
    ans, res = await sql_agent.answer_question(q)
    assert res.error is None
    assert res.row_count == 6
    assert any(r["label"] == "TNK-03-006" for r in res.results)


@pytest.mark.asyncio
async def test_benchmark_q7_fill_rate_by_tenant():
    q = "What is the fill rate (gallons delivered / gallons ordered) for completed orders by tenant?"
    ans, res = await sql_agent.answer_question(q)
    assert res.error is None
    assert res.row_count == 12  # All 12 tenants
    assert "fill_rate" in res.results[0]
    for r in res.results:
        assert 0.80 <= r["fill_rate"] <= 1.0


@pytest.mark.asyncio
async def test_benchmark_q8_declining_delivery_volume():
    q = "List tenants with declining delivery volume (compare last 30 days vs previous 30 days)"
    ans, res = await sql_agent.answer_question(q)
    assert res.error is None
    assert res.row_count > 0
    # Every returned tenant should have negative change
    for r in res.results:
        assert r["change"] < 0


@pytest.mark.asyncio
async def test_dynamic_time_ranges():
    # Test arbitrary 48 days for Tenant 1
    ans48, res48 = await sql_agent.answer_question("How many deliveries were completed in the last 48 days?", tenant_id=1)
    assert res48.error is None
    assert res48.results[0]["completed_deliveries"] == 210

    # Test arbitrary 4 days for Tenant 1
    ans4, res4 = await sql_agent.answer_question("How many deliveries were completed in the last 4 days?", tenant_id=1)
    assert res4.error is None
    assert res4.results[0]["completed_deliveries"] == 25

    # Test 7 days for Tenant 1
    ans7, res7 = await sql_agent.answer_question("How many deliveries were completed in the last 7 days?", tenant_id=1)
    assert res7.error is None
    assert res7.results[0]["completed_deliveries"] == 34


