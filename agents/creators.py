from datetime import datetime
import asyncio
import logging

from agents.base import build_agent, response_content
from tools.search import format_evidence, web_search
from utils.models import Creator, CreatorList, UserRequirement
from utils.settings import settings


async def _yt_evidence(query: str) -> str:
    results = await web_search(
        query=query,
        max_results=settings.max_creators,
        include_domains=["youtube.com"],
    )
    return format_evidence(results)


async def discover_creators(requirement: UserRequirement) -> list[Creator]:
    logging.info("discover_creators: %s", requirement.topic)

    queries = [
        f"{requirement.topic} for {requirement.current_level} in {requirement.preferred_language} {datetime.now().year}"
    ]
    
    blocks = await asyncio.gather(*[_yt_evidence(q) for q in queries], return_exceptions=True)
    evidence = "\n\n======\n\n".join(
        f"Query: {q}\n{b}" for q, b in zip(queries, blocks) if isinstance(b, str) and b.strip()
    )
    if not evidence.strip() or evidence.count("No evidence") == len(queries):
        raise RuntimeError(
            "YouTube search returned no creator evidence. Check py_yt / network."
        )

    agent = build_agent(
        name="Creator Discovery Agent",
        output_schema=CreatorList,
        instructions=[
            "Pick 3–5 YouTube educators from the search evidence only.",
            "Prefer technical depth and real teaching channels, not pure entertainment.",
            "Do not invent names, URLs, or audience claims.",
            "Every creator must map to at least one evidence URL from the results.",
            "Return exactly 3 to 5 creators (never an empty list).",
        ],
    )

    response = await response_content(
        agent,
        f"""User requirement:
{requirement.model_dump_json(indent=2)}

YouTube search evidence:
{evidence}

Return 3–5 creators grounded in the evidence above.""",
    )
    logging.info("creators: %s", [c.name for c in response.creators])
    return response.creators