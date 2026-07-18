from agents.base import build_agent, response_content
from tools.search import format_evidence, web_search
from utils.models import CourseCandidate, TopicResource, UserRequirement
from utils.settings import settings


def select_topic_resource(
    topic: str,
    requirement: UserRequirement,
    selected_course: CourseCandidate,
) -> TopicResource:
    results = web_search(
        query=f"{topic} tutorial {requirement.topic}",
        max_results=settings.max_resource_candidates,
        include_domains=["youtube.com"],
    )

    agent = build_agent(
        name="YouTube Resource Selector",
        output_schema=TopicResource,
        instructions=[
            "Choose exactly ONE YouTube resource for this topic.",
            "Do not return alternatives, playlists, or multiple URLs.",
            "Choose the resource that most directly fills the topic need.",
            "Prefer clear technical explanations, credible creators, and recent material.",
            "Avoid duplicate content already heavily covered by the selected course.",
            "Never invent a title, creator, or URL.",
        ],
    )

    return response_content(
        agent,
        f"""Learning topic: {topic}

User requirement:
{requirement.model_dump_json(indent=2)}

Selected primary course:
{selected_course.model_dump_json(indent=2)}

YouTube candidates:
{format_evidence(results)}

Return exactly one selected resource.""",
    )