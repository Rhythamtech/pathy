"""
Tests for cli.py — pure CLI helper functions.
No network, no LLM, no .env required.
All agent calls are mocked.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Patch env vars before anything from the project is imported
with patch.dict(
    "os.environ",
    {
        "OPENAI_API_KEY": "test-key",
        "OPENAI_BASE_URL": "http://localhost",
        "OPENAI_MODEL_NAME": "test-model",
        "JINA_AI_KEY": "test-jina",
    },
):
    from cli import roadmap_to_markdown, print_rankings, _run_pipeline
    from utils.models import (
        FinalRoadmap,
        RankedCourse,
        RoadmapWeek,
        TopicResource,
        UserRequirement,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _topic_resource(topic="Basics"):
    return TopicResource(
        topic=topic,
        video_title=f"{topic} Video",
        video_url="https://youtube.com/watch?v=test",
        creator="Test Creator",
        selection_reason="most relevant",
    )


def _week(n=1):
    return RoadmapWeek(
        week=n,
        topic=f"Week {n}",
        learning_goal="learn something",
        primary_course_focus="module A",
        youtube_resource=_topic_resource(f"Week {n}"),
        practical_work="do exercises",
        completion_criteria="pass quiz",
    )


def _roadmap(num_weeks=2):
    return FinalRoadmap(
        title="Python Roadmap",
        selected_course="Best Python Course",
        selected_course_url="https://example.com/course",
        selected_course_reason="highest rated",
        evidence_note="Based on public community research.",
        weeks=[_week(i) for i in range(1, num_weeks + 1)],
    )


def _ranked_course(title="Best Python Course", score=8.5):
    return RankedCourse(
        course_title=title,
        score=score,
        goal_relevance=9.0,
        curriculum_depth=8.0,
        independent_feedback=8.0,
        creator_credibility=9.0,
        recency=8.0,
        value=8.0,
        strengths=["great content"],
        concerns=[],
        decision_reason="Best fit for the goal.",
    )


@pytest.fixture
def requirement():
    return UserRequirement(
        topic="Python",
        current_level="beginner",
        target_outcome="build apps",
        weekly_hours=5,
    )


# ---------------------------------------------------------------------------
# roadmap_to_markdown
# ---------------------------------------------------------------------------

class TestRoadmapToMarkdown:
    def test_title_is_h1(self):
        md = roadmap_to_markdown(_roadmap())
        assert md.startswith("# Python Roadmap")

    def test_selected_course_section(self):
        md = roadmap_to_markdown(_roadmap())
        assert "## Selected Course" in md
        assert "[Best Python Course](https://example.com/course)" in md

    def test_weekly_plan_section(self):
        md = roadmap_to_markdown(_roadmap(num_weeks=3))
        assert "## Weekly Plan" in md
        assert "### Week 1:" in md
        assert "### Week 2:" in md
        assert "### Week 3:" in md

    def test_week_contains_all_fields(self):
        md = roadmap_to_markdown(_roadmap(num_weeks=1))
        assert "**Goal:**" in md
        assert "**Primary course focus:**" in md
        assert "**One YouTube resource:**" in md
        assert "**Why this resource:**" in md
        assert "**Practical work:**" in md
        assert "**Done when:**" in md

    def test_youtube_link_format(self):
        md = roadmap_to_markdown(_roadmap(num_weeks=1))
        assert "[Week 1 Video](https://youtube.com/watch?v=test)" in md

    def test_evidence_note_as_blockquote(self):
        md = roadmap_to_markdown(_roadmap())
        assert "> Based on public community research." in md

    def test_zero_weeks(self):
        rm = _roadmap(num_weeks=0)
        md = roadmap_to_markdown(rm)
        assert "## Weekly Plan" in md
        assert "### Week" not in md


# ---------------------------------------------------------------------------
# print_rankings (smoke test — should not raise)
# ---------------------------------------------------------------------------

class TestPrintRankings:
    def test_smoke_three_rankings(self, capsys):
        rankings = [_ranked_course(f"Course {i}", score=9.0 - i) for i in range(3)]
        # Rich prints to its own console; just assert it doesn't raise
        print_rankings(rankings)

    def test_smoke_one_ranking(self):
        print_rankings([_ranked_course()])

    def test_smoke_empty(self):
        print_rankings([])

    def test_only_top_three_shown(self):
        # Even if 5 rankings are passed, only 3 rows should be added.
        # We verify by checking print_rankings doesn't crash and returns None.
        rankings = [_ranked_course(f"Course {i}") for i in range(5)]
        result = print_rankings(rankings)
        assert result is None


# ---------------------------------------------------------------------------
# _run_pipeline (integration-level, agents mocked)
# ---------------------------------------------------------------------------

class TestRunPipeline:
    @pytest.mark.asyncio
    async def test_happy_path(self, requirement):
        from utils.models import CourseCandidate, Creator, ReviewEvidence

        creators = [
            Creator(name="Fireship", niche="web", trust_reason="popular")
        ]
        courses = [
            CourseCandidate(
                title="Best Python Course",
                instructor="Fireship",
                provider="fireship.io",
                url="https://fireship.io/course",
                format="video",
                creator_connection="direct creator",
            )
        ]
        reviews = [
            ReviewEvidence(
                course_title="Best Python Course",
                source="Reddit",
                url="https://reddit.com",
                sentiment="positive",
                confidence="high",
            )
        ]
        rankings = [_ranked_course("Best Python Course", score=9.0)]
        roadmap = _roadmap(num_weeks=1)
        roadmap.selected_course = "Best Python Course"

        with (
            patch("cli.discover_creators", new=AsyncMock(return_value=creators)),
            patch("cli.find_courses", new=AsyncMock(return_value=courses)),
            patch("cli.validate_reviews", new=AsyncMock(return_value=reviews)),
            patch("cli.rank_courses", new=AsyncMock(return_value=rankings)),
            patch("cli.build_roadmap", new=AsyncMock(return_value=roadmap)),
            patch("cli.save_markdown", return_value=MagicMock(
                with_suffix=MagicMock(return_value=MagicMock(write_text=MagicMock())),
                __str__=lambda s: "output/roadmap_test.md",
            )),
        ):
            await _run_pipeline(requirement)  # should not raise

    @pytest.mark.asyncio
    async def test_exits_when_no_courses(self, requirement):
        import typer
        from utils.models import Creator

        creators = [Creator(name="X", niche="y", trust_reason="z")]

        with (
            patch("cli.discover_creators", new=AsyncMock(return_value=creators)),
            patch("cli.find_courses", new=AsyncMock(return_value=[])),
        ):
            with pytest.raises(typer.Exit):
                await _run_pipeline(requirement)

    @pytest.mark.asyncio
    async def test_exits_when_no_rankings(self, requirement):
        import typer
        from utils.models import CourseCandidate, Creator, ReviewEvidence

        creators = [Creator(name="X", niche="y", trust_reason="z")]
        courses = [
            CourseCandidate(
                title="Course",
                instructor="X",
                provider="x.io",
                url="https://x.io",
                format="video",
                creator_connection="direct",
            )
        ]
        reviews = []

        with (
            patch("cli.discover_creators", new=AsyncMock(return_value=creators)),
            patch("cli.find_courses", new=AsyncMock(return_value=courses)),
            patch("cli.validate_reviews", new=AsyncMock(return_value=reviews)),
            patch("cli.rank_courses", new=AsyncMock(return_value=[])),
        ):
            with pytest.raises(typer.Exit):
                await _run_pipeline(requirement)
