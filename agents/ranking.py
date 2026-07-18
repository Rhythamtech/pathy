import logging
from agents.base import build_agent, response_content
from utils.models import (
    CourseCandidate,
    RankedCourse,
    RankedCourseList,
    ReviewEvidence,
    UserRequirement,
)


async def rank_courses(
    requirement: UserRequirement,
    courses: list[CourseCandidate],
    reviews: list[ReviewEvidence],
) -> list[RankedCourse]:
    logging.info(
        "Starting rank_courses. Candidates count: %d, Reviews count: %d",
        len(courses),
        len(reviews),
    )
    agent = build_agent(
        name="Course Ranking Agent",
        output_schema=RankedCourseList,
        instructions=[
            "Rank only the supplied candidates.",
            "Use this weighted score: goal relevance 30%, curriculum depth 20%, "
            "independent feedback 20%, creator credibility 15%, recency 10%, value 5%.",
            "Penalize missing syllabus, stale stack, repeated refund complaints, "
            "or an absence of independent evidence.",
            "Do not reward marketing claims without evidence.",
            "Clearly state concerns and uncertainty.",
            "Return candidates in descending score order.",
        ],
    )

    logging.info("Running Course Ranking Agent...")
    response = await response_content(
        agent,
        f"""Requirement:
{requirement.model_dump_json(indent=2)}

Courses:
{[course.model_dump() for course in courses]}

Review evidence:
{[review.model_dump() for review in reviews]}""",
    )
    logging.info(
        "Course ranking completed. Rankings: %s",
        [{r.course_title: r.score} for r in response.rankings]
    )
    return response.rankings