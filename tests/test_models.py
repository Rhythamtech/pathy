"""
Tests for utils/models.py — Pydantic model validation rules.
No network, no LLM, no .env required.
"""
import pytest
from pydantic import ValidationError

from utils.models import (
    CourseCandidate,
    Creator,
    FinalRoadmap,
    RankedCourse,
    ReviewEvidence,
    RoadmapWeek,
    TopicResource,
    UserRequirement,
)


# ---------------------------------------------------------------------------
# UserRequirement
# ---------------------------------------------------------------------------

class TestUserRequirement:
    def test_valid_defaults(self):
        req = UserRequirement(
            topic="Python",
            current_level="beginner",
            target_outcome="build apps",
            weekly_hours=5,
        )
        assert req.preferred_language == "English"

    def test_all_fields(self):
        req = UserRequirement(
            topic="ML",
            current_level="intermediate",
            target_outcome="get a job",
            weekly_hours=10,
            preferred_language="Hindi",
        )
        assert req.preferred_language == "Hindi"

    def test_missing_required_field(self):
        with pytest.raises(ValidationError):
            UserRequirement(topic="Python")  # missing required fields


# ---------------------------------------------------------------------------
# Creator
# ---------------------------------------------------------------------------

class TestCreator:
    def test_valid_minimal(self):
        c = Creator(name="Fireship", niche="web dev", trust_reason="popular")
        assert c.youtube_channel_url is None
        assert c.evidence_urls == []

    def test_with_urls(self):
        c = Creator(
            name="Traversy",
            niche="fullstack",
            trust_reason="trusted",
            evidence_urls=["https://youtube.com/@traversymedia"],
        )
        assert len(c.evidence_urls) == 1


# ---------------------------------------------------------------------------
# RankedCourse score bounds
# ---------------------------------------------------------------------------

class TestRankedCourse:
    def _base(self, **kwargs):
        defaults = dict(
            course_title="Test Course",
            score=7.0,
            goal_relevance=7.0,
            curriculum_depth=7.0,
            independent_feedback=7.0,
            creator_credibility=7.0,
            recency=7.0,
            value=7.0,
            strengths=["great"],
            concerns=[],
            decision_reason="solid",
        )
        defaults.update(kwargs)
        return RankedCourse(**defaults)

    def test_valid(self):
        r = self._base()
        assert r.score == 7.0

    def test_score_too_high(self):
        with pytest.raises(ValidationError):
            self._base(score=10.1)

    def test_score_too_low(self):
        with pytest.raises(ValidationError):
            self._base(score=-0.1)

    def test_score_boundaries(self):
        self._base(score=0.0)
        self._base(score=10.0)


# ---------------------------------------------------------------------------
# TopicResource
# ---------------------------------------------------------------------------

class TestTopicResource:
    def test_valid(self):
        r = TopicResource(
            topic="Async Python",
            video_title="Async IO in Python",
            video_url="https://youtube.com/watch?v=abc",
            creator="ArjanCodes",
            selection_reason="clear explanation",
        )
        assert r.topic == "Async Python"

    def test_missing_field(self):
        with pytest.raises(ValidationError):
            TopicResource(topic="x", video_title="y")  # missing required fields


# ---------------------------------------------------------------------------
# ReviewEvidence
# ---------------------------------------------------------------------------

class TestReviewEvidence:
    def test_valid_minimal(self):
        r = ReviewEvidence(
            course_title="Course A",
            source="Reddit",
            url="https://reddit.com/r/learnpython",
            sentiment="positive",
            confidence="high",
        )
        assert r.positive_themes == []
        assert r.negative_themes == []


# ---------------------------------------------------------------------------
# FinalRoadmap
# ---------------------------------------------------------------------------

def _make_topic_resource():
    return TopicResource(
        topic="Basics",
        video_title="Intro Video",
        video_url="https://youtube.com/watch?v=xyz",
        creator="Some Creator",
        selection_reason="best intro",
    )


def _make_week(n=1):
    return RoadmapWeek(
        week=n,
        topic=f"Week {n} topic",
        learning_goal="understand basics",
        primary_course_focus="module 1",
        youtube_resource=_make_topic_resource(),
        practical_work="build a hello world app",
        completion_criteria="app runs without errors",
    )


class TestFinalRoadmap:
    def test_valid_roadmap(self):
        rm = FinalRoadmap(
            title="Python Roadmap",
            selected_course="Primal Video Course",
            selected_course_url="https://primalvideo.com/course",
            selected_course_reason="top rated",
            evidence_note="based on public data",
            weeks=[_make_week(1), _make_week(2)],
        )
        assert len(rm.weeks) == 2
        assert rm.weeks[0].week == 1

    def test_empty_weeks_allowed(self):
        # Pydantic doesn't enforce min_length on weeks by default
        rm = FinalRoadmap(
            title="Empty Roadmap",
            selected_course="Course",
            selected_course_url="https://example.com",
            selected_course_reason="reason",
            evidence_note="note",
            weeks=[],
        )
        assert rm.weeks == []
