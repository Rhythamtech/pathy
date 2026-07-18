from __future__ import annotations

import asyncio
import logging
from typing import Any
from urllib.parse import quote

import httpx
from py_yt import VideosSearch

from utils.console import console
from utils.settings import settings


JINA_SEARCH_URL = "https://s.jina.ai/"
JINA_READER_URL = "https://r.jina.ai/"


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "X-Return-Format": "markdown",
        "User-Agent": "Pathy-RoadMap-AI/0.1",
    }

    if settings.JINA_AI_KEY:
        headers["Authorization"] = f"Bearer {settings.JINA_AI_KEY}"

    return headers


async def _youtube_search(query: str, max_results: int) -> list[dict[str, Any]]:
    """Search YouTube directly via py_yt (no API key required)."""
    search = VideosSearch(query, limit=max_results, language="en", region="US")
    data = await search.next()
    results = []
    for v in data.get("result", []):
        channel = v.get("channel", {})
        snippets = v.get("descriptionSnippet") or []
        snippet_text = "".join(s.get("text", "") for s in snippets)
        content = (
            f"Channel: {channel.get('name', '')}\n"
            f"Views: {v.get('viewCount', {}).get('text', '')}\n"
            f"Duration: {v.get('duration', '')}\n"
            f"Published: {v.get('publishedTime', '')}\n"
            f"Description: {snippet_text}"
        )
        results.append({
            "title": v.get("title", ""),
            "url": v.get("link", ""),
            "content": content,
            "score": 0,
        })
    logging.info("YouTube search returned %d results for query: '%s'", len(results), query)
    return results


def web_search(
    query: str,
    max_results: int = 5,
    include_domains: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Run one bounded search query.

    If include_domains contains 'youtube.com', uses py_yt (no API key).
    Otherwise falls back to Jina Search.
    """
    console.print(f"[dim]  → Searching web: '{query}'...[/dim]")

    if include_domains and "youtube.com" in include_domains:
        logging.info("YouTube search. Query: '%s', max_results: %d", query, max_results)
        return asyncio.run(_youtube_search(query, max_results))

    domain_filter = ""
    if include_domains:
        sites = " OR ".join(f"site:{domain}" for domain in include_domains)
        domain_filter = f" ({sites})"

    search_query = f"{query}{domain_filter}"
    url = f"{JINA_SEARCH_URL}{quote(search_query, safe='')}"

    logging.info(
        "Initiating Jina web search. Query: '%s', domains: %s, URL: %s",
        query,
        include_domains,
        url,
    )

    try:
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            response = client.get(url, headers=_headers())
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 422:
            logging.info(
                "Jina web search returned no results (422) for query: '%s'",
                query,
            )
            return []
        logging.error(
            "Jina web search HTTP error: Status %d, response: %s",
            e.response.status_code,
            e.response.text[:200],
            exc_info=True,
        )
        raise e
    except Exception as e:
        logging.error("Jina web search network/unexpected error: %s", str(e), exc_info=True)
        raise e

    results = _parse_search_response(
        payload=response.json() if _is_json(response) else response.text,
        max_results=max_results,
    )
    logging.info(
        "Jina web search completed. Found %d parsed results (requested %d).",
        len(results),
        max_results,
    )
    return results


def read_page(url: str, max_characters: int = 7000) -> str:
    """
    Fetch clean Markdown/text from a public URL through Jina Reader.
    """
    reader_url = f"{JINA_READER_URL}{quote(url, safe=':/?=&%')}"

    headers = _headers()
    headers["Accept"] = "text/plain"

    logging.info(
        "Reading web page through Jina Reader. URL: %s, Reader URL: %s",
        url,
        reader_url,
    )
    console.print(f"[dim]  → Reading page: {url}...[/dim]")

    try:
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            response = client.get(reader_url, headers=headers)
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logging.warning(
            "Jina Reader HTTP error for URL %s: Status %d",
            url,
            e.response.status_code,
        )
        raise e
    except Exception as e:
        logging.warning(
            "Jina Reader network/unexpected error for URL %s: %s",
            url,
            str(e),
        )
        raise e

    content = response.text[:max_characters]
    logging.info(
        "Successfully read page %s. Extracted content length: %d chars (max_characters %d).",
        url,
        len(content),
        max_characters,
    )
    return content


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