import asyncio
import json
import os
import urllib.request
import urllib.error
from agents import function_tool
from schemas.models import LibraryResolveResult, DocsResult


_SERVER_URL = "https://mcp.context7.com/mcp"


class _Context7Transport:
    """Minimal Streamable HTTP transport for the Context7 MCP server.

    Implements the two-step call sequence: initialize (handshake + session ID),
    then tools/call. One instance per logical tool invocation.
    """

    def __init__(self):
        self._req_id = 0
        self._session_id: str | None = None
        self._api_key = os.environ.get("CONTEXT7_API_KEY")

    def _post(self, payload: dict) -> dict:
        self._req_id += 1
        payload["id"] = self._req_id

        body = json.dumps(payload).encode()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": "desktop-agent/1.0",
        }
        if self._api_key:
            headers["CONTEXT7_API_KEY"] = self._api_key
        if self._session_id:
            headers["mcp-session-id"] = self._session_id

        req = urllib.request.Request(_SERVER_URL, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                sid = resp.headers.get("mcp-session-id")
                if sid:
                    self._session_id = sid
                raw = resp.read().decode()
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"HTTP {e.code}: {e.read().decode()}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"Network error: {e.reason}") from e

        # Server replies with SSE (text/event-stream): event: message\ndata: {...}\n\n
        # Extract the first non-empty data: line.
        data_line = None
        for line in raw.splitlines():
            stripped = line.strip()
            if stripped.startswith("data:"):
                data_line = stripped[len("data:"):].strip()
                if data_line:
                    break
        if data_line is not None:
            raw = data_line
        if not raw:
            raise RuntimeError("Context7 returned empty response")

        resp_json = json.loads(raw)
        if "error" in resp_json:
            err = resp_json["error"]
            raise RuntimeError(f"MCP error {err['code']}: {err['message']}")
        return resp_json["result"]

    def initialize(self) -> None:
        """MCP handshake — must be called before tools/call to obtain a session ID."""
        self._post({
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "desktop-agent", "version": "1.0.0"},
                "capabilities": {},
            },
        })

    def call_tool(self, name: str, arguments: dict) -> str:
        """Invoke a named MCP tool and return its concatenated text content."""
        result = self._post({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        })
        blocks = result.get("content", [])
        return "\n".join(b["text"] for b in blocks if b.get("type") == "text")


@function_tool
async def resolve_library_id(library_name: str) -> LibraryResolveResult:
    """Resolve a library or framework name to a Context7-compatible library ID.

    Always call this before fetch_library_docs to get the canonical library ID
    (e.g. /encode/httpx). Do not guess or invent the ID — always resolve it first.

    Args:
        library_name: Plain-English name, e.g. "python httpx" or "react hooks".
    """
    # MCP-over-HTTP tool: @function_tool wrapping an external JSON-RPC server.
    # The agent calls this exactly like read_file or search_files — the MCP Streamable
    # HTTP protocol is an implementation detail hidden inside _Context7Transport.
    # asyncio.to_thread runs the blocking urllib calls in a thread pool so the
    # event loop is never blocked on network I/O.
    def _run() -> str:
        transport = _Context7Transport()
        transport.initialize()
        return transport.call_tool(
            "resolve-library-id",
            {"query": library_name, "libraryName": library_name},
        )

    raw = await asyncio.to_thread(_run)

    # Extract the first library ID from the response text.
    # Format: "- Context7-compatible library ID: /org/project"
    library_id = ""
    for line in raw.splitlines():
        if "library ID:" in line:
            part = line.split("library ID:", 1)[1].strip()
            library_id = part.split()[0]
            break

    return LibraryResolveResult(library_id=library_id, raw=raw)


@function_tool
async def fetch_library_docs(library_id: str, query: str) -> DocsResult:
    """Fetch up-to-date documentation for a library from Context7.

    Call resolve_library_id first to obtain the library_id.
    Use this when the user asks about a library's API, configuration, or usage patterns.

    Args:
        library_id: Context7 library ID from resolve_library_id, e.g. "/encode/httpx".
        query: Topic to focus the docs on, e.g. "async client usage" or "authentication".
    """
    # [CONCEPT] asyncio.to_thread: runs blocking urllib I/O in a thread pool so the
    # event loop stays responsive while waiting for the network round-trip.
    def _run() -> str:
        transport = _Context7Transport()
        transport.initialize()
        return transport.call_tool(
            "query-docs",
            {"libraryId": library_id, "query": query},
        )

    raw = await asyncio.to_thread(_run)
    return DocsResult(library_id=library_id, query=query, content=raw)
