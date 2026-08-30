import logging
from typing import Any, Dict, Optional

from app.mcp.server import McpCallRequest, McpCallResponse, call_mcp_tool

logger = logging.getLogger("fleetpanda.mcp_client")


class McpClient:
    """
    Client for interacting with FleetPanda MCP Server tools, passing Bearer token authentication.
    """
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        bearer_token: Optional[str] = None
    ) -> McpCallResponse:
        """
        Invokes an MCP tool with Bearer authorization header.
        """
        auth_header = f"Bearer {bearer_token}" if bearer_token else None
        req = McpCallRequest(tool_name=tool_name, arguments=arguments)
        return await call_mcp_tool(req, authorization=auth_header)

    async def execute_sql(
        self,
        sql: str,
        tenant_id: Optional[int] = None,
        bearer_token: Optional[str] = None
    ) -> McpCallResponse:
        """Helper to invoke execute_sql_query via MCP."""
        args = {"sql": sql}
        if tenant_id is not None:
            args["tenant_id"] = tenant_id
        return await self.call_tool("execute_sql_query", args, bearer_token=bearer_token)

    async def get_customer_context(
        self,
        tenant_id: int,
        bearer_token: Optional[str] = None
    ) -> McpCallResponse:
        """Helper to invoke get_customer_context via MCP."""
        return await self.call_tool("get_customer_context", {"tenant_id": tenant_id}, bearer_token=bearer_token)

    async def search_kb(
        self,
        query: str,
        product_area: Optional[str] = None,
        bearer_token: Optional[str] = None
    ) -> McpCallResponse:
        """Helper to invoke search_knowledge_base via MCP."""
        args = {"query": query}
        if product_area:
            args["product_area"] = product_area
        return await self.call_tool("search_knowledge_base", args, bearer_token=bearer_token)


mcp_client = McpClient()

