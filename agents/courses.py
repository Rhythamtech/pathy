from datetime import datetime
from pydantic import BaseModel
from agents.base import build_agent, response_content
from tools.search import format_evidence, read_page, web_search
from utils.models import CourseCandidate, Creator, UserRequirement, CourseURL
from utils.settings import settings


def get_official_course_evidence(course_url: str) -> str:
    try:
        return read_page(course_url, max_characters=7000)
    except Exception:
        return ""


def find_courses(
    requirement: UserRequirement,
    creators: list[Creator],
) -> list[CourseCandidate]:
    creator_names = ", ".join(creator.name for creator in creators)

    # Search first
    results = web_search(
        query=(
            f"({creator_names}) {requirement.topic} "
            f" course cohort official syllabus {datetime.now().year - 1} {datetime.now().year}"
        ),
        max_results=8,
    )

    # Extract top official course page URLs
    url_agent = build_agent(
        name="Course URL Extractor",
        output_schema=list[CourseURL],
        instructions=[
            "Identify the top official direct course website URLs from the search results.",
            "Exclude social media, reviews, YouTube links, or directories.",
            "Only return direct official course landing/syllabus URLs.",
            "Limit to at most 3 top official URLs.",
        ],
    )

    candidate_urls = response_content(
        url_agent,
        f"Search results:\n{format_evidence(results)}",
    )

    # Read the top official pages
    official_evidence_blocks = []
    if candidate_urls:
        for item in candidate_urls:
            page_text = get_official_course_evidence(item.url)
            if page_text.strip():
                official_evidence_blocks.append(
                    f"Official URL: {item.url}\nContent:\n{page_text}"
                )

    official_evidence = "\n\n---\n\n".join(official_evidence_blocks)

    # Extract details using the official page content
    agent = build_agent(
        name="Course Research Agent",
        output_schema=list[CourseCandidate],
        instructions=[
            "Find only creator-led courses, cohorts, or bootcamps.",
            "The instructor must have a meaningful YouTube creator connection.",
            "Popular independent cohorts may be included if their instructor and syllabus are public.",
            "Exclude Udemy, DataCamp, Coursera, and generic marketplace courses.",
            "Prefer programs launched or updated in the most recent 6 to 8 months.",
            "Extract price, launch or update date, syllabus topics, and instructor details using the provided official page contents.",
            "Never invent launch dates, prices, syllabus topics, or URLs.",
            f"Return at most {settings.max_courses} candidates.",
        ],
    )

    return response_content(
        agent,
        f"""Requirement:
{requirement.model_dump_json(indent=2)}

Eligible YouTube creators:
{[creator.model_dump() for creator in creators]}

Web search evidence:
{format_evidence(results)}

Official course pages content:
{official_evidence}

Extract only verifiable eligible candidates, utilizing the official course page contents for specific details (price, dates, syllabus, instructor).""",
    )