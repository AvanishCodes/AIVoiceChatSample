import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import sqlglot
from sqlglot import exp

# SQLite Authorizer Action Codes
SQLITE_OK = 0
SQLITE_DENY = 1
SQLITE_IGNORE = 2

# Allowed SQLite operations for read-only analytical queries
ALLOWED_SQLITE_ACTIONS: Set[int] = {
    sqlite3.SQLITE_SELECT,
    sqlite3.SQLITE_READ,
    sqlite3.SQLITE_FUNCTION,
}

# Explicitly forbidden destructive / modifying actions
FORBIDDEN_SQLITE_ACTIONS: Set[int] = {
    sqlite3.SQLITE_INSERT,
    sqlite3.SQLITE_UPDATE,
    sqlite3.SQLITE_DELETE,
    sqlite3.SQLITE_PRAGMA,
    sqlite3.SQLITE_ATTACH,
    sqlite3.SQLITE_DETACH,
    sqlite3.SQLITE_ALTER_TABLE,
    sqlite3.SQLITE_DROP_TABLE,
    sqlite3.SQLITE_DROP_INDEX,
    sqlite3.SQLITE_DROP_VIEW,
    sqlite3.SQLITE_DROP_TRIGGER,
    sqlite3.SQLITE_CREATE_TABLE,
    sqlite3.SQLITE_CREATE_INDEX,
    sqlite3.SQLITE_CREATE_VIEW,
    sqlite3.SQLITE_CREATE_TRIGGER,
    sqlite3.SQLITE_TRANSACTION,
}

# Tables that require multi-tenant isolation
MULTI_TENANT_TABLES = {
    "customers",
    "drivers",
    "trucks",
    "delivery_orders",
    "shifts",
    "tank_readings",
}


class SecurityViolationError(Exception):
    """Raised when a query violates security policies or multi-tenant isolation."""
    def __init__(self, message: str, code: str = "SECURITY_VIOLATION"):
        super().__init__(message)
        self.message = message
        self.code = code


class CrossTenantAccessViolation(SecurityViolationError):
    """Raised when a user attempts to access data outside their scoped tenant."""
    def __init__(self, message: str):
        super().__init__(message, code="CROSS_TENANT_ACCESS_DENIED")


class DDLNotAllowedError(SecurityViolationError):
    """Raised when a query attempts DDL/DML data modification."""
    def __init__(self, message: str):
        super().__init__(message, code="DDL_DML_NOT_ALLOWED")


def sqlite_authorizer_callback(action_code: int, param1: Any, param2: Any, db_name: Any, trigger_name: Any) -> int:
    """
    SQLite authorizer callback.
    Blocks all DDL, DML, PRAGMA, ATTACH, and write operations at the database engine level.
    """
    if action_code in FORBIDDEN_SQLITE_ACTIONS:
        return SQLITE_DENY
    if action_code in ALLOWED_SQLITE_ACTIONS:
        return SQLITE_OK
    # Deny unknown or unexpected action codes
    return SQLITE_DENY


def get_readonly_connection(db_path: Path) -> sqlite3.Connection:
    """
    Creates a hardened, read-only SQLite connection.
    - Uses URI filename with mode=ro
    - Attaches strict SQLite query authorizer callback
    """
    db_uri = f"file:{db_path.resolve()}?mode=ro"
    conn = sqlite3.connect(db_uri, uri=True, timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.set_authorizer(sqlite_authorizer_callback)
    return conn


def validate_and_sanitize_sql(
    sql: str,
    enforce_tenant_id: Optional[int] = None,
    allow_cross_tenant: bool = False
) -> Tuple[str, List[str]]:
    """
    Validates SQL query using AST parsing (sqlglot).
    
    Guarantees:
    1. Only single SELECT statements are allowed (no semicolon injection, no multi-statements).
    2. Zero DDL/DML operations (CREATE, DROP, ALTER, INSERT, UPDATE, DELETE, PRAGMA, ATTACH).
    3. Multi-tenant isolation: If enforce_tenant_id is specified:
       - Confirms tenant_id = enforce_tenant_id is applied.
       - Rejects queries targeting a different tenant_id (CrossTenantAccessViolation).
    """
    warnings: List[str] = []
    
    # 1. Clean and strip trailing whitespace / comments
    sql_clean = sql.strip()
    if sql_clean.endswith(";"):
        sql_clean = sql_clean[:-1].strip()

    if not sql_clean:
        raise SecurityViolationError("SQL query cannot be empty")

    # 2. Parse statements with sqlglot
    try:
        parsed_statements = sqlglot.parse(sql_clean, read="sqlite")
    except Exception as e:
        raise SecurityViolationError(f"SQL Syntax Error: {str(e)}")

    if not parsed_statements:
        raise SecurityViolationError("No valid SQL statement found")

    if len(parsed_statements) > 1:
        raise SecurityViolationError(
            "Multiple SQL statements detected. Multi-statement execution is forbidden for security."
        )

    ast = parsed_statements[0]
    if ast is None:
        raise SecurityViolationError("Unable to parse SQL statement")

    # 3. Verify statement is strictly a SELECT statement
    if not isinstance(ast, exp.Select):
        raise DDLNotAllowedError(
            f"Only read-only SELECT queries are permitted. Detected statement type: {ast.key.upper()}"
        )

    # 4. Check for forbidden expression types
    forbidden_types = (
        exp.Insert, exp.Update, exp.Delete, exp.Create, exp.Drop, 
        exp.Alter, exp.Command, exp.Pragma, exp.Set
    )
    for forbidden in ast.find_all(forbidden_types):
        raise DDLNotAllowedError(f"Prohibited operation '{forbidden.key.upper()}' detected in query AST.")

    # 5. Multi-tenant isolation verification
    tables_in_query: Set[str] = set()
    for table_exp in ast.find_all(exp.Table):
        name = table_exp.name.lower()
        if name in MULTI_TENANT_TABLES:
            tables_in_query.add(name)

    if enforce_tenant_id is not None:
        # Check if the query queries multi-tenant tables
        if tables_in_query:
            # Look for tenant_id equality conditions
            found_tenant_filters: List[int] = []
            for eq in ast.find_all(exp.EQ):
                left_str = eq.left.sql().lower()
                right_str = eq.right.sql().lower()
                
                # Check for tenant_id = <val>
                if "tenant_id" in left_str:
                    try:
                        val = int(right_str)
                        found_tenant_filters.append(val)
                    except ValueError:
                        pass
                elif "tenant_id" in right_str:
                    try:
                        val = int(left_str)
                        found_tenant_filters.append(val)
                    except ValueError:
                        pass

            # Check if user is attempting cross-tenant access
            for t_filter in found_tenant_filters:
                if t_filter != enforce_tenant_id and not allow_cross_tenant:
                    raise CrossTenantAccessViolation(
                        f"Cross-tenant access violation: Current session is restricted to Tenant ID {enforce_tenant_id}, "
                        f"but query attempted to access Tenant ID {t_filter}."
                    )

            # If no tenant filter was found, we automatically inject or require tenant scoping
            if not found_tenant_filters and not allow_cross_tenant:
                ast = ast.where(f"tenant_id = {enforce_tenant_id}")
                sql_clean = ast.sql("sqlite")
                warnings.append(f"Auto-scoped query to enforce tenant_id = {enforce_tenant_id}")

    return sql_clean, warnings
