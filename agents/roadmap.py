from agents.base import build_agent, response_content
from agents.resources import select_topic_resource
from utils.models import (
    CourseCandidate,
    FinalRoadmap,
    RankedCourse,
    RoadmapWeek,
    UserRequirement,
)


def build_roadmap(
    requirement: UserRequirement,
    selected_course: CourseCandidate,
    ranking: RankedCourse,
) -> FinalRoadmap:
    planner = build_agent(
        name="Roadmap Planning Agent",
        output_schema=list[RoadmapWeek],
        instructions=[
            "Create a practical roadmap.",
            "Use the selected course as the primary learning spine.",
            "Respect the user's available weekly hours.",
            "Each week must have exactly one clearly scoped topic.",
            "Do not add YouTube resources yet.",
            "Include a practical task and measurable completion criteria per week.",
        ],
    )

    draft_weeks = response_content(
        planner,
        f"""Requirement:
{requirement.model_dump_json(indent=2)}

Selected course:
{selected_course.model_dump_json(indent=2)}

Why it won:
{ranking.model_dump_json(indent=2)}""",
    )

    complete_weeks: list[RoadmapWeek] = []

    for week in draft_weeks:
        resource = select_topic_resource(
            topic=week.topic,
            requirement=requirement,
            selected_course=selected_course,
        )

        complete_weeks.append(
            RoadmapWeek(
                week=week.week,
                topic=week.topic,
                learning_goal=week.learning_goal,
                primary_course_focus=week.primary_course_focus,
                youtube_resource=resource,
                practical_work=week.practical_work,
                completion_criteria=week.completion_criteria,
            )
        )

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