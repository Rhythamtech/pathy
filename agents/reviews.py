import logging
from agents.base import build_agent, response_content
from tools.search import format_evidence, web_search
from utils.models import CourseCandidate, ReviewEvidence, ReviewEvidenceList
from utils.settings import settings


def validate_reviews(courses: list[CourseCandidate]) -> list[ReviewEvidence]:
    logging.info("Starting validate_reviews for %d courses...", len(courses))
    evidence: list[dict] = []

    for course in courses:
        query = f'"{course.title}" reviews Reddit community feedback'
        logging.info("Searching Reddit feedback for '%s' with query: '%s'", course.title, query)
        results = web_search(
            query=query,
            max_results=settings.max_reviews_per_course,
            include_domains=["reddit.com"],
        )
        logging.info("Found %d Reddit search results for '%s'", len(results), course.title)
        evidence.append(
            {
                "course_title": course.title,
                "search_results": results,
            }
        )

    agent = build_agent(
        name="Review Validation Agent",
        output_schema=ReviewEvidenceList,
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

    logging.info("Running Review Validation Agent on compiled feedback evidence...")
    response = response_content(agent, f"Public feedback evidence:\n\n{formatted}")
    logging.info(
        "Review validation completed. Validated reviews: %s",
        [{r.course_title: r.confidence} for r in response.reviews]
    )
    return response.reviews