from datetime import timedelta
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.config import settings
from app.core.auth import (
    DEMO_USERS_DB,
    TokenResponse,
    User,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
)

auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class DemoUserPublic(BaseModel):
    email: str
    name: str
    role: str
    tenant_id: Any
    tenant_name: Any
    description: str


@auth_router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """Authenticate user with email and password, returning JWT access & refresh tokens."""
    user = authenticate_user(req.email, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "user_id": user.user_id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "tenant_id": user.tenant_id,
            "tenant_name": user.tenant_name,
            "permissions": user.permissions,
        }
    )


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshRequest):
    """Issue a new access token using a valid refresh token."""
    payload = decode_token(req.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token type - refresh token required",
        )

    email = payload.get("email")
    user = DEMO_USERS_DB.get(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
        )

    new_access_token = create_access_token(user)
    new_refresh_token = create_refresh_token(user)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "user_id": user.user_id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "tenant_id": user.tenant_id,
            "tenant_name": user.tenant_name,
            "permissions": user.permissions,
        }
    )


@auth_router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Returns profile and active tenant context of currently authenticated user."""
    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
        "tenant_id": current_user.tenant_id,
        "tenant_name": current_user.tenant_name,
        "permissions": current_user.permissions,
    }


@auth_router.get("/demo-users", response_model=List[DemoUserPublic])
async def get_demo_users():
    """Returns pre-configured demo user accounts for rapid testing and login."""
    return [
        DemoUserPublic(
            email="csm@fleetpanda.com",
            name="Arcadio (Lead CSM)",
            role="csm",
            tenant_id=None,
            tenant_name="FleetPanda HQ (Global Multi-Tenant)",
            description="Full visibility across all tenants and dispatch databases."
        ),
        DemoUserPublic(
            email="support@fleetpanda.com",
            name="Support Agent Maria",
            role="support_agent",
            tenant_id=None,
            tenant_name="FleetPanda HQ (Global Support)",
            description="Global support agent with cross-tenant triage & SQL query access."
        ),
        DemoUserPublic(
            email="admin@cascadefuel.com",
            name="Cascade Fuel Admin",
            role="tenant_admin",
            tenant_id=1,
            tenant_name="Cascade Fuel Services (Tenant 1)",
            description="Strictly scoped to Cascade Fuel. MCP blocks access to other tenants."
        ),
        DemoUserPublic(
            email="dispatcher@heartland.com",
            name="Heartland Propane Dispatcher",
            role="dispatcher",
            tenant_id=2,
            tenant_name="Heartland Propane (Tenant 2)",
            description="Strictly scoped to Heartland Propane."
        ),
        DemoUserPublic(
            email="ops@summitenergy.com",
            name="Summit Energy Ops Lead",
            role="tenant_admin",
            tenant_id=3,
            tenant_name="Summit Energy Group (Tenant 3)",
            description="Strictly scoped to Summit Energy Group ($96k CARR, Health 91)."
        ),
        DemoUserPublic(
            email="admin@desertsun.com",
            name="Desert Sun Petro Admin",
            role="tenant_admin",
            tenant_id=4,
            tenant_name="Desert Sun Petroleum (Tenant 4)",
            description="Strictly scoped to Desert Sun Petroleum (Health 28, Contract 2026-07-15)."
        ),
        DemoUserPublic(
            email="manager@timberridge.com",
            name="Timber Ridge Oil Manager",
            role="tenant_admin",
            tenant_id=8,
            tenant_name="Timber Ridge Oil (Tenant 8)",
            description="Strictly scoped to Timber Ridge Oil (Health 39, Contract 2026-09-10)."
        ),
    ]

