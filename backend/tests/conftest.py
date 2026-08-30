import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.core.auth import DEMO_USERS_DB, create_access_token
from app.main import app


@pytest.fixture(scope="session")
def client():
    """FastAPI Test Client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def csm_token():
    """Access token for Global CSM (cross-tenant access)."""
    user = DEMO_USERS_DB["csm@fleetpanda.com"]
    return create_access_token(user)


@pytest.fixture
def tenant1_token():
    """Access token for Cascade Fuel Services (Tenant ID: 1)."""
    user = DEMO_USERS_DB["admin@cascadefuel.com"]
    return create_access_token(user)


@pytest.fixture
def tenant4_token():
    """Access token for Desert Sun Petroleum (Tenant ID: 4)."""
    user = DEMO_USERS_DB["admin@desertsun.com"]
    return create_access_token(user)

