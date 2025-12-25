"""MCP client for bundestag-mcp server.

Async client that handles MCP session initialization and tool calls
via JSON-RPC over HTTP. Fetches Plenarprotokolle and other data from
the Bundestag DIP API through the MCP server.
"""

import asyncio
import json
from typing import Any

import httpx


class BundestagMCPClient:
    """Client to interact with bundestag-mcp server via MCP protocol."""

    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url.rstrip("/")
        self.session_id: str | None = None
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=120.0)
        await self._initialize_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    async def _initialize_session(self) -> None:
        """Initialize MCP session with the server."""
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "noun-analysis", "version": "0.1.0"},
            },
        }

        response = await self._client.post(
            f"{self.base_url}/mcp",
            json=init_request,
            headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
        )
        response.raise_for_status()

        self.session_id = response.headers.get("mcp-session-id")

        if "text/event-stream" in response.headers.get("content-type", ""):
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data = json.loads(line[5:].strip())
                    if "result" in data:
                        break
        else:
            data = response.json()

        await self._send_initialized()

    async def _send_initialized(self) -> None:
        """Send initialized notification."""
        notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }
        headers = {"Content-Type": "application/json"}
        if self.session_id:
            headers["mcp-session-id"] = self.session_id

        await self._client.post(f"{self.base_url}/mcp", json=notification, headers=headers)

    async def call_tool(self, name: str, arguments: dict[str, Any] = None) -> Any:
        """Call an MCP tool and return the result."""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments or {}},
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.session_id:
            headers["mcp-session-id"] = self.session_id

        # Retry logic for transient errors
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await self._client.post(f"{self.base_url}/mcp", json=request, headers=headers)
                response.raise_for_status()
                break
            except (httpx.ReadError, httpx.ConnectError, httpx.TimeoutException) as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        if "text/event-stream" in response.headers.get("content-type", ""):
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data = json.loads(line[5:].strip())
                    if "result" in data:
                        return self._parse_tool_result(data["result"])
        else:
            data = response.json()
            if "result" in data:
                return self._parse_tool_result(data["result"])

        return None

    def _parse_tool_result(self, result: dict) -> Any:
        """Parse MCP tool result content."""
        if "content" in result and isinstance(result["content"], list):
            for item in result["content"]:
                if item.get("type") == "text":
                    try:
                        return json.loads(item["text"])
                    except json.JSONDecodeError:
                        return item["text"]
        return result

    async def search_speeches(
        self,
        query: str = "",
        limit: int = 100,
        party: str | None = None,
        wahlperiode: int | None = None,
        score_threshold: float = 0.0,
    ) -> list[dict]:
        """Search for speeches using bundestag_search_speeches tool."""
        args = {"query": query, "limit": limit}
        if party:
            args["party"] = party
        if wahlperiode:
            args["wahlperiode"] = wahlperiode
        if score_threshold:
            args["scoreThreshold"] = score_threshold

        result = await self.call_tool("bundestag_search_speeches", args)

        if isinstance(result, dict) and "results" in result:
            return result["results"]
        return result if isinstance(result, list) else []

    async def get_all_speeches_by_party(
        self,
        party: str,
        wahlperiode: int = 20,
        batch_size: int = 100,
        max_speeches: int | None = None,
    ) -> list[dict]:
        """Fetch all speeches for a party (legacy method using chunked search)."""
        all_speeches = []
        offset = 0

        while True:
            speeches = await self.search_speeches(
                query="",
                limit=batch_size,
                party=party,
                wahlperiode=wahlperiode,
            )

            if not speeches:
                break

            all_speeches.extend(speeches)

            if max_speeches and len(all_speeches) >= max_speeches:
                all_speeches = all_speeches[:max_speeches]
                break

            if len(speeches) < batch_size:
                break

            offset += batch_size
            await asyncio.sleep(0.1)

        return all_speeches

    async def search_plenarprotokolle(
        self,
        wahlperiode: int = 20,
        limit: int = 100,
        cursor: str | None = None,
    ) -> dict:
        """Search for Plenarprotokolle.

        Returns dict with 'results', 'cursor', 'hasMore' keys.
        """
        args = {
            "wahlperiode": wahlperiode,
            "limit": limit,
        }
        if cursor:
            args["cursor"] = cursor

        result = await self.call_tool("bundestag_search_plenarprotokolle", args)

        if isinstance(result, dict):
            return {
                "results": result.get("results", []),
                "cursor": result.get("cursor"),
                "hasMore": result.get("hasMore", False),
                "totalResults": result.get("totalResults", 0),
            }
        return {"results": [], "cursor": None, "hasMore": False, "totalResults": 0}

    async def get_plenarprotokoll(
        self,
        protocol_id: int,
        include_full_text: bool = True,
    ) -> dict | None:
        """Get a single Plenarprotokoll by ID.

        Args:
            protocol_id: The numeric ID of the protocol
            include_full_text: Whether to include the full text

        Returns:
            Dict with protocol data and optionally 'fullText' key
        """
        result = await self.call_tool("bundestag_get_plenarprotokoll", {
            "id": protocol_id,
            "includeFullText": include_full_text,
        })

        if isinstance(result, dict) and result.get("success"):
            return {
                "data": result.get("data", {}),
                "fullText": result.get("fullText", ""),
            }
        return None

    async def get_all_protocol_ids(
        self,
        wahlperiode: int = 20,
        herausgeber: str = "BT",
        max_protocols: int = 0,
        progress_callback=None,
    ) -> list[dict]:
        """Fetch all protocol metadata using cursor pagination.

        Args:
            wahlperiode: Legislative period
            herausgeber: Publisher filter ('BT' for Bundestag)
            max_protocols: Maximum protocols to fetch (0 = all)
            progress_callback: Optional callback(count, message)

        Returns:
            List of protocol metadata dicts with 'id', 'dokumentnummer', etc.
        """
        all_protocols = []
        cursor = None
        page = 0
        empty_pages = 0

        while True:
            page += 1
            print(f"  Fetching protocol list page {page} ({len(all_protocols)} protocols so far)...", flush=True)
            if progress_callback:
                progress_callback(len(all_protocols), f"Fetching protocol list (page {page})...")

            result = await self.search_plenarprotokolle(
                wahlperiode=wahlperiode,
                limit=100,
                cursor=cursor,
            )

            protocols = [p for p in result.get("results", []) if p.get("herausgeber") == herausgeber]

            if not protocols:
                empty_pages += 1
                if empty_pages >= 3:
                    print(f"  No more {herausgeber} protocols found after {page} pages.", flush=True)
                    break
            else:
                empty_pages = 0
                all_protocols.extend(protocols)

            if max_protocols > 0 and len(all_protocols) >= max_protocols:
                return all_protocols[:max_protocols]

            cursor = result.get("cursor")
            if not cursor or not result.get("hasMore", False):
                break

        return all_protocols

    async def get_speeches_from_protocols(
        self,
        wahlperiode: int = 20,
        max_protocols: int = 10,
        herausgeber: str = "BT",
        progress_callback=None,
        batch_size: int = 10,
        parse_speeches_func=None,
    ) -> dict[str, list[dict]]:
        """Fetch speeches from Plenarprotokolle, grouped by party.

        Args:
            wahlperiode: Legislative period (default 20)
            max_protocols: Maximum number of protocols to fetch (0 = all)
            herausgeber: Publisher filter ('BT' for Bundestag, 'BR' for Bundesrat)
            progress_callback: Optional callback(current, total, protocol_name)
            batch_size: Number of protocols to fetch concurrently
            parse_speeches_func: Function to parse speeches from protocol text

        Returns:
            Dict mapping party names to lists of speech dicts
        """
        speeches_by_party: dict[str, list[dict]] = {}

        # Get all protocol IDs with proper pagination
        protocols = await self.get_all_protocol_ids(
            wahlperiode=wahlperiode,
            herausgeber=herausgeber,
            max_protocols=max_protocols,
            progress_callback=lambda count, msg: progress_callback(count, 0, msg) if progress_callback else None,
        )

        total = len(protocols)
        completed = 0

        # Process in batches for concurrent fetching
        for batch_start in range(0, total, batch_size):
            batch = protocols[batch_start:batch_start + batch_size]

            # Fetch batch concurrently
            async def fetch_one(protocol):
                protocol_id = protocol.get("id")
                if not protocol_id:
                    return None
                return await self.get_plenarprotokoll(int(protocol_id))

            results = await asyncio.gather(*[fetch_one(p) for p in batch])

            # Process results
            for protocol, full_protocol in zip(batch, results):
                completed += 1
                doc_nr = protocol.get("dokumentnummer", "?")

                if progress_callback:
                    progress_callback(completed, total, doc_nr)

                if not full_protocol:
                    continue

                full_text = full_protocol.get("fullText", "")
                if not full_text:
                    continue

                # Parse speeches from protocol (requires parse function to be passed)
                if parse_speeches_func:
                    speeches = parse_speeches_func(full_text)

                    # Group by party
                    for speech in speeches:
                        party = speech["party"]
                        if party not in speeches_by_party:
                            speeches_by_party[party] = []
                        speeches_by_party[party].append(speech)

        return speeches_by_party


async def test_connection(base_url: str = "http://localhost:3000") -> bool:
    """Test connection to the MCP server."""
    try:
        async with BundestagMCPClient(base_url) as client:
            # Try to search for protocols (doesn't require indexed data)
            result = await client.search_plenarprotokolle(limit=1)
            return result.get("totalResults", 0) > 0
    except Exception as e:
        print(f"Connection failed: {e}")
        return False
