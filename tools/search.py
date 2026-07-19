from __future__ import annotations

import asyncio
import logging
import re
from typing import Any
from urllib.parse import quote

import httpx
from youtube_search import YoutubeSearch

from utils.console import console
from utils.settings import settings

JINA_SEARCH = "https://s.jina.ai/"
JINA_READER = "https://r.jina.ai/"
_YT_ID = re.compile(r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})")


def _headers(accept: str = "application/json") -> dict[str, str]:
    h = {"Accept": accept, "X-Return-Format": "markdown", "User-Agent": "Pathy-RoadMap-AI/0.1"}
    if settings.JINA_AI_KEY:
        h["Authorization"] = f"Bearer {settings.JINA_AI_KEY}"
    return h


async def web_search(
    query: str,
    max_results: int = 5,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
) -> list[dict[str, Any]]:
    console.print(f"[dim]  → Searching: '{query}'...[/dim]")

    if include_domains and "youtube.com" in include_domains:
        results = await asyncio.to_thread(
            lambda: YoutubeSearch(query, max_results=max_results).to_dict()
        )
        return [
            {
                "title": v.get("title", ""),
                "url": f"https://www.youtube.com{v.get('url_suffix', '')}",
                "content": (
                    f"Channel: {v.get('channel', '')}\n"
                    f"Views: {v.get('views', '')}\n"
                    f"Duration: {v.get('duration', '')}\n"
                    f"Published: {v.get('publish_time', '')}\n"
                    f"Description: {v.get('long_desc', '') or ''}"
                ),
                "score": 0,
            }
            for v in results
        ]

    parts = [query]
    if include_domains:
        parts.append("(" + " OR ".join(f"site:{d}" for d in include_domains) + ")")
    if exclude_domains:
        parts.extend(f"-site:{d}" for d in exclude_domains)

    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            r = await client.get(f"{JINA_SEARCH}{quote(' '.join(parts), safe='')}", headers=_headers())
            r.raise_for_status()
    except httpx.HTTPStatusError as e:
        if e.response.status_code in (402, 422, 429):
            return []
        raise

    if "application/json" not in r.headers.get("content-type", ""):
        return [{"title": "Jina Search Result", "url": "", "content": r.text[:6000], "score": 0}]

    items = (r.json().get("data") or r.json().get("results") or r.json().get("items") or [])
    return [
        {
            "title": i.get("title", "Untitled"),
            "url": i.get("url") or i.get("link") or "",
            "content": (i.get("description") or i.get("content") or i.get("snippet") or "")[:1500],
            "score": i.get("score", 0),
        }
        for i in items[:max_results]
    ]


async def read_page(url: str, max_characters: int = 7000) -> str:
    console.print(f"[dim]  → Reading: {url}...[/dim]")
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        r = await client.get(
            f"{JINA_READER}{quote(url, safe=':/?=&%')}",
            headers=_headers(accept="text/plain"),
        )
        r.raise_for_status()
    return r.text[:max_characters]


def format_evidence(results: list[dict[str, Any]]) -> str:
    if not results:
        return "No evidence found."
    return "\n\n".join(
        f"SOURCE {i}\nTitle: {r['title']}\nURL: {r['url']}\nSnippet: {r['content']}"
        for i, r in enumerate(results, 1)
    )