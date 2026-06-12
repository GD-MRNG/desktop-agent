import asyncio
import os
import re
import httpx
from agents import function_tool
from schemas.models import SearchMatch, SearchResults, WebResult, WebSearchResults


@function_tool
async def search_files(directory: str, query: str) -> SearchResults:
    """Search files in a directory for lines matching a query string.

    Searches recursively through all text files. Returns matching lines with
    file paths and line numbers.

    Args:
        directory: Directory to search in. Use '.' for current directory.
        query: Text or pattern to search for.
    """
    # [CONCEPT] Tool chaining — the agent typically calls read_file after this
    # to load the full context of a matching file. The match result gives it
    # enough to decide which file is worth reading.
    matches: list[SearchMatch] = []
    pattern = re.compile(re.escape(query), re.IGNORECASE)

    for root, _dirs, files in os.walk(directory):
        # Skip hidden directories and common noise
        _dirs[:] = [d for d in _dirs if not d.startswith(".") and d not in ("__pycache__", ".venv", "node_modules")]
        for filename in files:
            if not _is_text_file(filename):
                continue
            filepath = os.path.join(root, filename)
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    for lineno, line in enumerate(f, start=1):
                        if pattern.search(line):
                            matches.append(SearchMatch(
                                file=filepath,
                                line_number=lineno,
                                line_content=line.rstrip("\n"),
                            ))
            except (OSError, PermissionError):
                continue

    return SearchResults(matches=matches, total=len(matches), query=query)


@function_tool
async def web_search(query: str) -> WebSearchResults:
    """Search the web for current information about a topic.

    Uses DuckDuckGo Instant Answer API. Returns titles, URLs, and snippets.

    Args:
        query: Search query string.
    """
    # [CONCEPT] External API integration as a tool.
    # asyncio.gather() in gather_search (agent/manager.py) can run this
    # concurrently with search_files when the agent needs both.
    results: list[WebResult] = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"},
            )
            data = response.json()

        # Abstract answer
        if data.get("AbstractText"):
            results.append(WebResult(
                title=data.get("Heading", "Summary"),
                url=data.get("AbstractURL", ""),
                snippet=data["AbstractText"],
            ))

        # Related topics
        for topic in data.get("RelatedTopics", [])[:5]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append(WebResult(
                    title=topic.get("Text", "")[:60],
                    url=topic.get("FirstURL", ""),
                    snippet=topic.get("Text", ""),
                ))
    except Exception as exc:
        results.append(WebResult(
            title="Search unavailable",
            url="",
            snippet=f"Could not retrieve results: {exc}",
        ))

    return WebSearchResults(results=results, query=query)


def _is_text_file(filename: str) -> bool:
    text_extensions = {
        ".py", ".txt", ".md", ".json", ".yaml", ".yml", ".toml",
        ".cfg", ".ini", ".env", ".sh", ".js", ".ts", ".html", ".css",
        ".rst", ".csv", ".xml", ".sql",
    }
    _, ext = os.path.splitext(filename)
    return ext.lower() in text_extensions
