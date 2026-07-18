import logging
from agno.tools.function import Function

from agents.base import build_agent, response_content
from tools.search import format_evidence, web_search
from utils.models import CourseCandidate, ReviewEvidence, ReviewEvidenceList
from utils.settings import settings


async def _search_reviews(query: str) -> str:
    """Search Reddit for course reviews and feedback."""
    results = await web_search(
        query=query,
        max_results=settings.max_reviews_per_course,
        include_domains=["reddit.com"],
    )
    return format_evidence(results)


async def validate_reviews(courses: list[CourseCandidate]) -> list[ReviewEvidence]:
    logging.info("Starting validate_reviews for %d courses...", len(courses))

    agent = build_agent(
        name="Review Validation Agent",
        output_schema=ReviewEvidenceList,
        tools=[
            Function(
                name="search_reviews",
                description="Search Reddit for feedback on specific courses using a custom query.",
                entrypoint=_search_reviews,
            )
        ],
        instructions=[
            "Use the `search_reviews` tool to search for community feedback on each provided course.",
            "Review feedback is evidence, not absolute truth.",
            "Prioritize recent independent and specific feedback.",
            "Treat testimonials from the provider website as low confidence.",
            "A vague opinion is weaker than feedback describing actual modules, projects, mentors, refunds, or support.",
            "Do not fabricate reviews when evidence is missing.",
            "Return one concise review assessment per course.",
        ],
    )

    course_data = "\n".join([f"- {c.title}" for c in courses])

    logging.info("Running Review Validation Agent on courses...")
    response = await response_content(
        agent,
        f"Courses to validate:\n{course_data}\n\nPlease search for reviews and validate them."
    )
    logging.info(
        "Review validation completed. Validated reviews: %s",
        [{r.course_title: r.confidence} for r in response.reviews]
    )
    return response.reviews