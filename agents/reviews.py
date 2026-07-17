from agents.base import build_agent, response_content
from tools.search import format_evidence, web_search
from utils.models import CourseCandidate, ReviewEvidence
from utils.settings import settings


def validate_reviews(courses: list[CourseCandidate]) -> list[ReviewEvidence]:
    evidence: list[dict] = []

    for course in courses:
        results = web_search(
            query=f'"{course.title}" reviews Reddit community feedback',
            max_results=settings.max_reviews_per_course,
            include_domains=["reddit.com"],
        )
        evidence.append(
            {
                "course_title": course.title,
                "search_results": results,
            }
        )

    agent = build_agent(
        name="Review Validation Agent",
        output_schema=list[ReviewEvidence],
        instructions=[
            "Review feedback is evidence, not absolute truth.",
            "Prioritize recent independent and specific feedback.",
            "Treat testimonials from the provider website as low confidence.",
            "A vague opinion is weaker than feedback describing actual modules, projects, mentors, refunds, or support.",
            "Do not fabricate reviews when evidence is missing.",
            "Return one concise review assessment per course.",
        ],
    )

    formatted = "\n\n".join(
        f"""COURSE: {item["course_title"]}
{format_evidence(item["search_results"])}"""
        for item in evidence
    )

    return response_content(agent, f"Public feedback evidence:\n\n{formatted}")