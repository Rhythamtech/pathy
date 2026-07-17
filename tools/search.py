from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

from utils.settings import settings

JINA_SEARCH_URL = "https://s.jina.ai/"
JINA_READER_URL = "https://r.jina.ai/"


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "X-Return-Format": "markdown",
        "User-Agent": "Pathy-RoadMap-AI/0.1",
    }

    if settings.jina_api_key:
        headers["Authorization"] = f"Bearer {settings.jina_api_key}"

    return headers


def web_search(
    query: str,
    max_results: int = 5,
    include_domains: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Run one bounded Jina Search query.

    Domain filtering is applied locally because the simple Jina Reader-style
    search endpoint is query based. Include site:domain filters in the query.
    """
    domain_filter = ""

    if include_domains:
        sites = " OR ".join(f"site:{domain}" for domain in include_domains)
        domain_filter = f" ({sites})"

    search_query = f"{query}{domain_filter}"
    url = f"{JINA_SEARCH_URL}{quote(search_query, safe='')}"

    with httpx.Client(timeout=30, follow_redirects=True) as client:
        response = client.get(url, headers=_headers())
        response.raise_for_status()

    return _parse_search_response(
        payload=response.json() if _is_json(response) else response.text,
        max_results=max_results,
    )


def read_page(url: str, max_characters: int = 7000) -> str:
    """
    Fetch clean Markdown/text from a public URL through Jina Reader.
    """
    reader_url = f"{JINA_READER_URL}{quote(url, safe=':/?=&%')}"

    headers = _headers()
    headers["Accept"] = "text/plain"

    with httpx.Client(timeout=30, follow_redirects=True) as client:
        response = client.get(reader_url, headers=headers)
        response.raise_for_status()

    return response.text[:max_characters]


def _is_json(response: httpx.Response) -> bool:
    content_type = response.headers.get("content-type", "")
    return "application/json" in content_type


def _parse_search_response(
    payload: dict[str, Any] | str,
    max_results: int,
) -> list[dict[str, Any]]:
    """
    Supports Jina JSON response shapes and a safe fallback when the service
    returns Markdown/text.
    """
    if isinstance(payload, dict):
        raw_results = (
            payload.get("data")
            or payload.get("results")
            or payload.get("items")
            or []
        )

        parsed: list[dict[str, Any]] = []

        for item in raw_results[:max_results]:
            parsed.append(
                {
                    "title": item.get("title", "Untitled result"),
                    "url": item.get("url", item.get("link", "")),
                    "content": (
                        item.get("description")
                        or item.get("content")
                        or item.get("snippet")
                        or ""
                    )[:1500],
                    "score": item.get("score", 0),
                }
            )

        return parsed

    return [
        {
            "title": "Jina Search Result",
            "url": "",
            "content": payload[:6000],
            "score": 0,
        }
    ]


def format_evidence(results: list[dict[str, Any]]) -> str:
    if not results:
        return "No evidence found."

    blocks = []

    for index, result in enumerate(results, start=1):
        blocks.append(
            f"""SOURCE {index}
Title: {result["title"]}
URL: {result["url"]}
Snippet: {result["content"]}"""
        )

    return "\n\n".join(blocks)