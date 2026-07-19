from datetime import datetime
import asyncio
import logging
import re
from urllib.parse import urlparse

from agents.base import build_agent, response_content
from tools.search import read_page, web_search
from utils.models import (
    CourseCandidate,
    CourseCandidateList,
    CourseURLList,
    Creator,
    UserRequirement,
)
from utils.settings import settings

_URL_RE = re.compile(r"https?://[^\s,)]+")
_SKIP_HOSTS = {
    "twitter.com", "x.com", "instagram.com", "linkedin.com",
    "facebook.com", "tiktok.com", "reddit.com",
}


def _course_urls(text: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for m in _URL_RE.finditer(text):
        url = m.group(0).rstrip(".,;:!?")
        host = urlparse(url).netloc
        if host and host not in _SKIP_HOSTS and url not in seen:
            seen.add(url)
            out.append(url)
    return out


async def _yt_course_block(query: str) -> str:
    results = await web_search(query, max_results=5, include_domains=["youtube.com"])
    if not results:
        return "No results found."
    blocks = []
    for r in results:
        desc = r.get("content", "")
        urls = _course_urls(desc)
        url_lines = "\n".join(f"  - {u}" for u in urls) if urls else "  (none)"
        blocks.append(
            f"Video: {r['title']}\nURL: {r['url']}\n{desc}\nExternal URLs:\n{url_lines}"
        )
    return "\n\n---\n\n".join(blocks)


async def find_courses(
    requirement: UserRequirement,
    creators: list[Creator],
) -> list[CourseCandidate]:
    if not creators:
        raise ValueError("Creator discovery returned no creators.")

    queries = [f"{c.name} {requirement.topic} course cohort bootcamp for {requirement.current_level} in {requirement.preferred_language} {datetime.now().year}." 
                for c in creators[:3]]

    raw = await asyncio.gather(*[_yt_course_block(q) for q in queries], return_exceptions=True)
    search_context = "\n\n======\n\n".join(
        f"Search query: {q}\n\n{r}"
        for q, r in zip(queries, raw)
        if not isinstance(r, Exception)
    )

    url_agent = build_agent(
        name="Course URL Extractor",
        output_schema=CourseURLList,
        instructions=[
            "Extract official course landing page URLs from YouTube search results.",
            "Use external URLs in video descriptions. If no external landing page is found, you may use the YouTube video or playlist URL itself as the course URL.",
            "Skip social media links (twitter, instagram, linkedin, facebook, tiktok) and directories.",
            "Only direct official course, syllabus, or playlist URLs. Max 3.",
        ],
    )
    urls_resp = await response_content(
        url_agent,
        f"""Requirement:
{requirement.model_dump_json(indent=2)}

Creators: {[c.model_dump() for c in creators]}

YouTube results:
{search_context}

Extract official course landing page URLs only.""",
    )
    candidate_urls = urls_resp.urls

    # Filter out YouTube URLs from Jina reading to avoid 402 / proxy blocking
    read_urls = [item for item in candidate_urls if "youtube.com" not in item.url and "youtu.be" not in item.url]
    
    evidence_parts: list[str] = []
    if read_urls:
        pages = await asyncio.gather(
            *[read_page(item.url, max_characters=7000) for item in read_urls],
            return_exceptions=True,
        )
        for item, page in zip(read_urls, pages):
            if isinstance(page, str) and page.strip():
                evidence_parts.append(f"Official URL: {item.url}\nContent:\n{page}")

    agent = build_agent(
        name="Course Research Agent",
        output_schema=CourseCandidateList,
        instructions=[
            "Find creator-led courses, cohorts, or bootcamps with a YouTube creator link.",
            "Exclude Udemy, DataCamp, Coursera, and generic marketplaces.",
            "Prefer programs launched/updated in the last 6–8 months.",
            "Use search context or official page content for price, dates, syllabus, instructor.",
            "Never invent facts or URLs.",
            f"Return at most {settings.max_courses} candidates.",
        ],
    )
    response = await response_content(
        agent,
        f"""Requirement:
{requirement.model_dump_json(indent=2)}

Creators: {[c.model_dump() for c in creators]}

YouTube Search Context (use this for details on YouTube-hosted courses):
{search_context}

Official pages (use this for details on external courses):
{"\n\n---\n\n".join(evidence_parts)}

Extract only verifiable eligible candidates.""",
    )
    return response.courses