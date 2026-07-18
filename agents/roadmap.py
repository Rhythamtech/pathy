import asyncio
import logging
from agno.tools.function import Function

from agents.base import build_agent, response_content
from agents.resources import select_topic_resource
from utils.console import console
from utils.models import (
    CourseCandidate,
    FinalRoadmap,
    RankedCourse,
    RoadmapWeek,
    RoadmapWeekList,
    UserRequirement,
)


async def build_roadmap(
    requirement: UserRequirement,
    selected_course: CourseCandidate,
    ranking: RankedCourse,
) -> FinalRoadmap:
    import json

    logging.info("Starting build_roadmap for selected course: '%s'", selected_course.title)
    planner = build_agent(
        name="Roadmap Planning Agent",
        output_schema=RoadmapWeekList,
        instructions=[
            "Create a practical roadmap.",
            "Use the selected course as the primary learning spine.",
            "Respect the user's available weekly hours.",
            "Each week must have exactly one clearly scoped topic.",
            "Do not add YouTube resources yet.",
            "Include a practical task and measurable completion criteria per week.",
            'Return valid JSON only, with no Markdown fences and exactly this top-level shape: {"weeks": [...]}.',
            'Since "youtube_resource" is a required field of TopicResource type but should not be selected yet, set it to a dummy object: {"topic": "", "video_title": "", "video_url": "", "creator": "", "selection_reason": ""}.',
        ],
    )

    logging.info("Running Roadmap Planning Agent...")
    draft_weeks_resp = await response_content(
        planner,
        f"""Requirement:
{requirement.model_dump_json(indent=2)}

Selected course:
{selected_course.model_dump_json(indent=2)}

Why it won:
{ranking.model_dump_json(indent=2)}""",
    )

    if isinstance(draft_weeks_resp, RoadmapWeekList):
        roadmap_week_list = draft_weeks_resp
    elif isinstance(draft_weeks_resp, str):
        cleaned = draft_weeks_resp.strip()
        if cleaned.startswith("```"):
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
        try:
            data = json.loads(cleaned)
        except Exception as e:
            logging.error("Failed to parse agent response as JSON: %s. Cleaned: %r", str(e), cleaned)
            raise ValueError(f"Failed to parse agent response as JSON: {e}. Cleaned content: {cleaned}") from e
        roadmap_week_list = RoadmapWeekList.model_validate(data)
    elif isinstance(draft_weeks_resp, dict):
        roadmap_week_list = RoadmapWeekList.model_validate(draft_weeks_resp)
    else:
        raise TypeError(f"Unexpected response type from Roadmap Planning Agent: {type(draft_weeks_resp)} (value: {draft_weeks_resp!r})")

    draft_weeks = roadmap_week_list.weeks
    logging.info("Drafted roadmap with %d weeks.", len(draft_weeks))

    # Select YouTube resources for all weeks concurrently
    async def _select_resource(week):
        logging.info("Selecting YouTube resource for Week %d topic: '%s'", week.week, week.topic)
        console.print(f"[dim]  → Searching YouTube for Week {week.week} resource: '{week.topic}'...[/dim]")
        resource = await select_topic_resource(
            topic=week.topic,
            requirement=requirement,
            selected_course=selected_course,
        )
        logging.info(
            "Selected resource for Week %d topic '%s': '%s' by %s (%s)",
            week.week,
            week.topic,
            resource.video_title,
            resource.creator,
            resource.video_url,
        )
        return week, resource

    results = await asyncio.gather(*[_select_resource(week) for week in draft_weeks])

    complete_weeks: list[RoadmapWeek] = [
        RoadmapWeek(
            week=week.week,
            topic=week.topic,
            learning_goal=week.learning_goal,
            primary_course_focus=week.primary_course_focus,
            youtube_resource=resource,
            practical_work=week.practical_work,
            completion_criteria=week.completion_criteria,
        )
        for week, resource in results
    ]

    logging.info("Finished building final roadmap with %d complete weeks.", len(complete_weeks))
    return FinalRoadmap(
        title=f"{requirement.topic} Learning Roadmap",
        selected_course=selected_course.title,
        selected_course_url=selected_course.url,
        selected_course_reason=ranking.decision_reason,
        evidence_note=(
            "Recommendation is based on bounded public research, official course "
            "information, and sampled independent community feedback."
        ),
        weeks=complete_weeks,
    )