from agno.tools.function import Function

from agents.base import build_agent, response_content
from tools.search import format_evidence, web_search
from utils.models import Creator, UserRequirement
from utils.settings import settings


def discover_creators(requirement: UserRequirement) -> list[Creator]:
    results = web_search(
        query=(
            f"best YouTube creators teaching {requirement.topic} "
            f"for {requirement.current_level} "
        ),
        max_results=settings.max_creators,
        include_domains=["youtube.com"],
    )

    agent = build_agent(
        name="Creator Discovery Agent",
        output_schema=list[Creator],
        tools=[
            Function(
                name="search_web",
                description="Search web evidence when supplied evidence is insufficient.",
                entrypoint=web_search,
            )
        ],
        instructions=[
            "Select only 3 to 5 relevant YouTube creators.",
            "Prioritize educators with technical depth and a real public audience.",
            "Do not select influencers based purely on subscriber count.",
            "Do not invent channel URLs or audience claims.",
            "Every selection must be grounded in supplied evidence.",
        ],
    )

    return response_content(
        agent,
        f"""User requirement:
{requirement.model_dump_json(indent=2)}

Search evidence:
{format_evidence(results)}

Return creators appropriate for this roadmap.""",
    )