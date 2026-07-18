import logging
from datetime import datetime
from agents.base import build_agent, response_content
from tools.search import format_evidence, read_page, web_search
from utils.models import CourseCandidate, Creator, UserRequirement, CourseURLList, CourseCandidateList
from utils.settings import settings


def get_official_course_evidence(course_url: str) -> str:
    logging.info("Attempting to get official course evidence from URL: %s", course_url)
    try:
        content = read_page(course_url, max_characters=7000)
        logging.info("Successfully fetched %d chars of course evidence from %s", len(content), course_url)
        return content
    except Exception as e:
        logging.warning("Failed to fetch official course evidence from %s: %s", course_url, str(e))
        return ""


def find_courses(
    requirement: UserRequirement,
    creators: list[Creator],
) -> list[CourseCandidate]:
    logging.info("Starting find_courses...")
    if not creators:
        logging.error("Creator discovery returned no creators.")
        raise ValueError("Creator discovery returned no creators.")

    if not all(isinstance(creator, Creator) for creator in creators):
        received = [type(creator).__name__ for creator in creators]
        logging.error("Expected list[Creator] from discover_creators(), received: %s", received)
        raise TypeError(
            "Expected list[Creator] from discover_creators(), "
            f"received: {received}"
        )

    results = []
    # Try searching for each creator individually to get high-quality targeted results
    # and avoid complex, malformed queries that might fail Jina search.
    for creator in creators[:3]:  # Top 3 creators
        creator_query = (
            f'"{creator.name}" '
            f"lastest course or cohort for {requirement.topic}"
        )
        try:
            creator_results = web_search(query=creator_query, max_results=3)
            results.extend(creator_results)
        except Exception as e:
            logging.warning("Web search failed for creator '%s': %s", creator.name, e)

    # Fallback/general query to make sure we don't miss general creator-led courses
    general_query = (
        f"{requirement.topic} "
        f"lastest course or cohort."
    )
    try:
        general_results = web_search(query=general_query, max_results=4)
        results.extend(general_results)
    except Exception as e:
        logging.warning("General course web search failed: %s", e)

    # Remove duplicates by URL
    seen_urls = set()
    unique_results = []
    for r in results:
        url = r.get("url")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_results.append(r)
    results = unique_results[:8]
    logging.info("Course discovery web search combined and returned %d items.", len(results))

    # Extract top official course page URLs
    url_agent = build_agent(
        name="Course URL Extractor",
        output_schema=CourseURLList,
        instructions=[
            "Identify the top official direct course website URLs from the search results.",
            "Exclude social media, reviews, YouTube links, or directories.",
            "Only return direct official course landing/syllabus URLs.",
            "Limit to at most 3 top official URLs.",
        ],
    )

    logging.info("Extracting candidate course page URLs...")
    candidate_urls_resp = response_content(
        url_agent,
        f"Search results:\n{format_evidence(results)}",
    )
    candidate_urls = candidate_urls_resp.urls
    logging.info("Candidate URLs extracted: %s", [item.url for item in candidate_urls])

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
    logging.info("Syllabus evidence blocks fetched: %d", len(official_evidence_blocks))

    # Extract details using the official page content
    agent = build_agent(
        name="Course Research Agent",
        output_schema=CourseCandidateList,
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

    logging.info("Researching course details using official page contents and web search results...")
    response = response_content(
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
    logging.info(
        "Course discovery completed. Found courses: %s",
        [c.title for c in response.courses]
    )
    return response.courses