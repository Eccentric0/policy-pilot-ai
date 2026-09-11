from __future__ import annotations

import asyncio
import json
import sys
from typing import Any


def call_mcp_tool(name: str, arguments: dict[str, Any], timeout_seconds: int = 20) -> dict[str, Any]:
    """Call the standalone MCP server over stdio when MCP_MODE=stdio."""

    async def invoke() -> dict[str, Any]:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "app.mcp_server.server"],
        )
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(name, arguments)
                if getattr(result, "is_error", False):
                    return {"success": False, "data": None, "error_code": "MCP_ERROR", "message": str(result), "source": name}
                blocks = getattr(result, "structured_content", None)
                if blocks:
                    return blocks if isinstance(blocks, dict) else json.loads(json.dumps(blocks))
                text_blocks = getattr(result, "content", [])
                for block in text_blocks:
                    if getattr(block, "text", None):
                        return json.loads(block.text)
                return {"success": False, "data": None, "error_code": "EMPTY_MCP_RESULT", "message": "MCP 返回为空", "source": name}

    try:
        return asyncio.run(asyncio.wait_for(invoke(), timeout=timeout_seconds))
    except Exception as exc:
        return {"success": False, "data": None, "error_code": "MCP_CALL_FAILED", "message": str(exc), "source": name}
