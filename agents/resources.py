from datetime import datetime
from agno.tools.function import Function

from agents.base import build_agent, response_content
from tools.search import format_evidence, web_search
from utils.models import CourseCandidate, TopicResource, UserRequirement
from utils.settings import settings


async def _search_youtube_resources(query: str) -> str:
    """Search YouTube for relevant topic resources."""
    results = await web_search(
        query=query,
        max_results=settings.max_resource_candidates,
        include_domains=["youtube.com"],
    )
    return format_evidence(results)


async def select_topic_resource(
    topic: str,
    requirement: UserRequirement,
    selected_course: CourseCandidate,
) -> TopicResource:

    agent = build_agent(
        name="YouTube Resource Selector",
        output_schema=TopicResource,
        tools=[
            Function(
                name="search_youtube_resources",
                description="Search YouTube for relevant resources using a custom query.",
                entrypoint=_search_youtube_resources,
            )
        ],
        instructions=[
            f"Use the `search_youtube_resources` tool to run searches and find relevant YouTube videos for the topic. You can also add {datetime.now().year} to the query to get the latest resources.",
            "Choose exactly ONE YouTube resource for this topic.",
            "Do not return alternatives, playlists, or multiple URLs.",
            "Choose the resource that most directly fills the topic need.",
            "Prefer clear technical explanations, credible creators, and recent material.",
            "Avoid duplicate content already heavily covered by the selected course.",
            "Never invent a title, creator, or URL.",
        ],
    )

    return await response_content(
        agent,
        f"""Learning topic: {topic}

User requirement:
{requirement.model_dump_json(indent=2)}

Selected primary course:
{selected_course.model_dump_json(indent=2)}

Return exactly one selected resource.""",
    )