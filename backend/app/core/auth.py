import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.config import settings

# Security Bearer scheme
security = HTTPBearer(auto_error=False)

def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Securely hash a password with PBKDF2 HMAC SHA-256."""
    if not salt:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"{salt}${key.hex()}"

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against stored salt$hash."""
    try:
        salt, key_hex = hashed.split("$")
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
        return hmac.compare_digest(key.hex(), key_hex)
    except Exception:
        return False


class User(BaseModel):
    user_id: str
    email: str
    name: str
    role: str  # "csm", "support_agent", "tenant_admin", "dispatcher"
    tenant_id: Optional[int] = None  # None indicates Global/FleetPanda internal staff
    tenant_name: Optional[str] = None
    permissions: List[str] = ["read", "query_sql", "triage_tickets"]
    hashed_password: str


# Pre-configured demo users across roles and tenants
DEMO_USERS_DB: Dict[str, User] = {
    "csm@fleetpanda.com": User(
        user_id="usr-csm-01",
        email="csm@fleetpanda.com",
        name="Arcadio (Lead CSM)",
        role="csm",
        tenant_id=None,
        tenant_name="FleetPanda HQ (Global)",
        permissions=["read", "query_sql", "triage_tickets", "cross_tenant"],
        hashed_password=hash_password("password123", salt="csm_salt_2026")
    ),
    "support@fleetpanda.com": User(
        user_id="usr-sup-01",
        email="support@fleetpanda.com",
        name="Support Agent Maria",
        role="support_agent",
        tenant_id=None,
        tenant_name="FleetPanda HQ (Global)",
        permissions=["read", "query_sql", "triage_tickets", "cross_tenant"],
        hashed_password=hash_password("password123", salt="sup_salt_2026")
    ),
    "admin@cascadefuel.com": User(
        user_id="usr-ten1-01",
        email="admin@cascadefuel.com",
        name="Cascade Fuel Dispatch Manager",
        role="tenant_admin",
        tenant_id=1,
        tenant_name="Cascade Fuel Services",
        permissions=["read", "query_sql", "triage_tickets"],
        hashed_password=hash_password("password123", salt="ten1_salt_2026")
    ),
    "dispatcher@heartland.com": User(
        user_id="usr-ten2-01",
        email="dispatcher@heartland.com",
        name="Heartland Propane Dispatcher",
        role="dispatcher",
        tenant_id=2,
        tenant_name="Heartland Propane",
        permissions=["read", "query_sql", "triage_tickets"],
        hashed_password=hash_password("password123", salt="ten2_salt_2026")
    ),
    "ops@summitenergy.com": User(
        user_id="usr-ten3-01",
        email="ops@summitenergy.com",
        name="Summit Energy Ops Lead",
        role="tenant_admin",
        tenant_id=3,
        tenant_name="Summit Energy Group",
        permissions=["read", "query_sql", "triage_tickets"],
        hashed_password=hash_password("password123", salt="ten3_salt_2026")
    ),
    "admin@desertsun.com": User(
        user_id="usr-ten4-01",
        email="admin@desertsun.com",
        name="Desert Sun Petro Admin",
        role="tenant_admin",
        tenant_id=4,
        tenant_name="Desert Sun Petroleum",
        permissions=["read", "query_sql", "triage_tickets"],
        hashed_password=hash_password("password123", salt="ten4_salt_2026")
    ),
    "manager@timberridge.com": User(
        user_id="usr-ten8-01",
        email="manager@timberridge.com",
        name="Timber Ridge Oil Manager",
        role="tenant_admin",
        tenant_id=8,
        tenant_name="Timber Ridge Oil",
        permissions=["read", "query_sql", "triage_tickets"],
        hashed_password=hash_password("password123", salt="ten8_salt_2026")
    ),
}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: Dict[str, Any]


class TokenPayload(BaseModel):
    sub: str
    email: str
    name: str
    role: str
    tenant_id: Optional[int] = None
    tenant_name: Optional[str] = None
    permissions: List[str] = []
    type: str  # "access" or "refresh"
    exp: int


def create_access_token(user: User, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": user.user_id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "tenant_id": user.tenant_id,
        "tenant_name": user.tenant_name,
        "permissions": user.permissions,
        "type": "access",
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user: User, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT refresh token."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    payload = {
        "sub": user.user_id,
        "email": user.email,
        "type": "refresh",
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def authenticate_user(email: str, password: str) -> Optional[User]:
    """Authenticate user by email and password."""
    user = DEMO_USERS_DB.get(email.lower().strip())
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> User:
    """Extract and validate the current authenticated user from Bearer token."""
    if not credentials or not credentials.credentials:
        # Fallback for unauthenticated dev/guest mode: return Global CSM demo user
        return DEMO_USERS_DB["csm@fleetpanda.com"]

    token = credentials.credentials
    payload = decode_token(token)
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type - access token required",
        )
        
    email = payload.get("email")
    user = DEMO_USERS_DB.get(email)
    if not user:
        # Construct ephemeral user from valid token claims
        user = User(
            user_id=payload.get("sub", "usr-ephemeral"),
            email=email or "unknown@fleetpanda.com",
            name=payload.get("name", "Authenticated User"),
            role=payload.get("role", "support_agent"),
            tenant_id=payload.get("tenant_id"),
            tenant_name=payload.get("tenant_name"),
            permissions=payload.get("permissions", ["read"]),
            hashed_password="",
        )
    return user

