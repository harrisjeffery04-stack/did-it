"""Demo bridge — the browser talks to this tiny HTTP app; this app talks MCP.

The bridge exists so the voice-first web demo can drive the REAL MCP server
over the REAL Streamable HTTP transport — the same path Alexa+ uses. One
backend, two front-ends: proof that the integration is the open standard,
not a mock.
"""
import json
import os

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from starlette.applications import Starlette
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Route

MCP_URL = os.environ.get("PROVENDONE_MCP_URL", "http://127.0.0.1:8765/mcp")
HERE = os.path.dirname(os.path.abspath(__file__))


async def _call(tool: str, args: dict) -> dict:
    """One MCP round-trip per request (server runs stateless streamable HTTP)."""
    async with streamablehttp_client(MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as s:
            await s.initialize()
            res = await s.call_tool(tool, args)
            data = getattr(res, "structuredContent", None)
            if isinstance(data, dict):
                return data
            return json.loads(res.content[0].text) if res.content else {}


async def home(request):
    return FileResponse(os.path.join(HERE, "index.html"))


async def health(request):
    return JSONResponse({"ok": True, "mcp_url": MCP_URL})


async def task(request):
    body = await request.json()
    receipt = await _call("run_task", {"task": body.get("task", ""),
                                      "steps": body.get("steps")})
    return JSONResponse(receipt)


async def receipt(request):
    return JSONResponse(await _call("get_receipt",
                                    {"receipt_id": request.path_params["rid"]}))


async def receipts_list(request):
    limit = int(request.query_params.get("limit", "10"))
    return JSONResponse(await _call("list_receipts", {"limit": limit}))


app = Starlette(routes=[
    Route("/", home),
    Route("/healthz", health),
    Route("/api/task", task, methods=["POST"]),
    Route("/api/receipt/{rid}", receipt),
    Route("/api/receipts", receipts_list),
])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.environ.get("BRIDGE_HOST", "127.0.0.1"),
                port=int(os.environ.get("BRIDGE_PORT", "8770")))