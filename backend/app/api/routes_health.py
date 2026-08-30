from typing import Any, Dict, List
from fastapi import APIRouter

from app.config import settings
from app.data_layer.data_loader import data_loader

health_router = APIRouter(prefix="/api", tags=["Health & Metadata"])


@health_router.get("/health")
async def health_check():
    """Health check endpoint displaying system state, database connectivity, and data counts."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "llm_provider": settings.LLM_PROVIDER,
        "database": {
            "path": str(settings.DATABASE_PATH),
            "exists": settings.DATABASE_PATH.exists(),
        },
        "loaded_data": {
            "customers_count": len(data_loader.customers),
            "aliases_count": len(data_loader.aliases),
            "tickets_count": len(data_loader.tickets),
            "transcripts_count": len(data_loader.transcripts),
            "kb_articles_count": len(data_loader.kb_articles),
        }
    }


@health_router.get("/tenants")
async def list_tenants():
    """Returns all 12 tenant profiles with aliases and operational status."""
    results = []
    for tenant_id, cust in data_loader.customers.items():
        aliases = [a.alias for a in data_loader.aliases if a.tenant_id == tenant_id]
        results.append({
            "tenant_id": tenant_id,
            "name": cust.name,
            "health_score": cust.health_score,
            "carr": cust.carr,
            "modules_active": cust.modules_active,
            "contract_end_date": cust.contract_end_date,
            "assigned_csm": cust.assigned_csm,
            "fleet_size": cust.fleet_size,
            "region": cust.region,
            "aliases": aliases,
        })
    return sorted(results, key=lambda x: x["tenant_id"])

