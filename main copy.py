import json
import logging
from datetime import datetime
from typing import Optional

import typer
from rich.table import Table

from agents.courses import find_courses
from agents.creators import discover_creators
from agents.ranking import rank_courses
from agents.reviews import validate_reviews
from agents.roadmap import build_roadmap
from utils.console import console, heading, save_markdown, status
from utils.logging import setup_logging
from utils.models import FinalRoadmap, UserRequirement

app = typer.Typer(
    add_completion=False,
    pretty_exceptions_show_locals=False,
)


def ask_requirement() -> UserRequirement:
    heading("Pathy RoadMap AI")

    topic = typer.prompt("What do you want to learn?")
    current_level = typer.prompt(
        "Your current level",
        default="beginner",
    )
    target_outcome = typer.prompt(
        "What outcome do you want?",
        default="Build production-ready projects",
    )
    weekly_hours = typer.prompt(
        "Hours available per week",
        default=8,
        type=int,
    )

    has_budget = typer.confirm("Do you have a course budget?", default=True)

    budget_inr: Optional[int] = None

    if has_budget:
        budget_inr = typer.prompt(
            "Maximum budget in INR",
            default=10000,
            type=int,
        )

    preferred_language = typer.prompt(
        "Preferred learning language",
        default="English",
    )

    return UserRequirement(
        topic=topic,
        current_level=current_level.lower(),
        target_outcome=target_outcome,
        weekly_hours=weekly_hours,
        budget_inr=budget_inr,
        preferred_language=preferred_language,
    )


def print_rankings(rankings) -> None:
    table = Table(title="Ranked Course Candidates", show_lines=True)
    table.add_column("Rank", style="cyan", width=6)
    table.add_column("Course", style="bold")
    table.add_column("Score", justify="right")
    table.add_column("Why", width=55)

    for index, item in enumerate(rankings[:3], start=1):
        table.add_row(
            str(index),
            item.course_title,
            f"{item.score:.1f}/10",
            item.decision_reason,
        )

    console.print(table)


def roadmap_to_markdown(roadmap: FinalRoadmap) -> str:
    lines = [
        f"# {roadmap.title}",
        "",
        "## Selected Course",
        f"**[{roadmap.selected_course}]({roadmap.selected_course_url})**",
        "",
        roadmap.selected_course_reason,
        "",
        f"> {roadmap.evidence_note}",
        "",
        "## Weekly Plan",
        "",
    ]

    for week in roadmap.weeks:
        lines.extend(
            [
                f"### Week {week.week}: {week.topic}",
                "",
                f"**Goal:** {week.learning_goal}",
                "",
                f"**Primary course focus:** {week.primary_course_focus}",
                "",
                (
                    f"**One YouTube resource:** "
                    f"[{week.youtube_resource.video_title}]"
                    f"({week.youtube_resource.video_url}) "
                    f"by {week.youtube_resource.creator}"
                ),
                "",
                f"**Why this resource:** {week.youtube_resource.selection_reason}",
                "",
                f"**Practical work:** {week.practical_work}",
                "",
                f"**Done when:** {week.completion_criteria}",
                "",
            ]
        )

    return "\n".join(lines)


@app.command()
def start() -> None:
    setup_logging()
    logging.info("Starting Pathy RoadMap AI workflow.")

    requirement = ask_requirement()
    logging.info("User requirements: %s", requirement.model_dump_json())

    with status("Finding relevant YouTube creators..."):
        logging.info("Starting creator discovery...")
        creators = discover_creators(requirement)
        logging.info("Discovered creators: %s", [c.name for c in creators])

    with status("Researching creator-led courses and cohorts..."):
        logging.info("Starting course discovery...")
        courses = find_courses(requirement, creators)
        logging.info("Discovered courses: %s", [c.title for c in courses])

    if not courses:
        logging.warning("No eligible creator-led courses were found.")
        console.print(
            "[bold red]No eligible creator-led courses were found.[/bold red]"
        )
        raise typer.Exit(code=1)

    with status("Checking sampled public feedback..."):
        logging.info("Starting review validation...")
        reviews = validate_reviews(courses)
        logging.info("Validated reviews: %s", [r.course_title for r in reviews])

    with status("Ranking course candidates..."):
        logging.info("Starting course ranking...")
        rankings = rank_courses(requirement, courses, reviews)
        logging.info("Ranked course scores: %s", [{r.course_title: r.score} for r in rankings])

    if not rankings:
        logging.error("Could not rank any valid course candidates.")
        console.print("[bold red]Could not rank any valid course candidates.[/bold red]")
        raise typer.Exit(code=1)

    print_rankings(rankings)

    selected_ranking = rankings[0]
    logging.info("Top ranked course: %s with score %s", selected_ranking.course_title, selected_ranking.score)
    selected_course = next(
        course
        for course in courses
        if course.title == selected_ranking.course_title
    )

    with status("Building your roadmap and selecting one video per topic..."):
        logging.info("Building roadmap and picking topic resources...")
        roadmap = build_roadmap(
            requirement=requirement,
            selected_course=selected_course,
            ranking=selected_ranking,
        )
        logging.info("Roadmap successfully built: %s", roadmap.title)

    markdown = roadmap_to_markdown(roadmap)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    markdown_path = save_markdown(f"roadmap_{timestamp}.md", markdown)
    logging.info("Saved roadmap markdown to %s", markdown_path)

    json_path = markdown_path.with_suffix(".json")
    json_path.write_text(
        json.dumps(roadmap.model_dump(), indent=2),
        encoding="utf-8",
    )
    logging.info("Saved research JSON to %s", json_path)

    console.print()
    console.print(markdown)
    console.print()
    console.print(
        f"[bold green]Saved roadmap:[/bold green] {markdown_path}"
    )
    console.print(
        f"[bold green]Saved research JSON:[/bold green] {json_path}"
    )


if __name__ == "__main__":
    app()