from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import quote

import httpx
from py_yt import Video, VideosSearch

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
        data = await VideosSearch(query, limit=max_results, language="en", region="US").next()
        out = []
        for v in data.get("result", []):
            ch = v.get("channel") or {}
            snip = "".join(s.get("text", "") for s in (v.get("descriptionSnippet") or []))
            out.append({
                "title": v.get("title", ""),
                "url": v.get("link", ""),
                "content": f"Channel: {ch.get('name', '')}\nViews: {(v.get('viewCount') or {}).get('text', '')}\n"
                           f"Duration: {v.get('duration', '')}\nPublished: {v.get('publishedTime', '')}\nDescription: {snip}",
                "score": 0,
            })
        return out

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
    if "youtube.com" in url or "youtu.be" in url:
        if not _YT_ID.search(url):
            return ""
        try:
            data = await Video.get(url, timeout=5)
        except Exception as e:
            logging.warning("py_yt failed for %s: %s", url, e)
            return ""
        if not isinstance(data, dict):
            return ""
        ch, views = data.get("channel") or {}, data.get("viewCount") or {}
        desc = data.get("description") or data.get("shortDescription") or ""
        return "\n".join([
            f"Title: {data.get('title') or ''}",
            f"Channel: {ch.get('name', '') if isinstance(ch, dict) else ''}",
            f"Views: {views.get('text', '') if isinstance(views, dict) else ''}",
            f"Duration: {data.get('duration') or ''}",
            f"Description: {desc[:2000]}",
        ])

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