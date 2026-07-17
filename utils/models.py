from pydantic import BaseModel, Field


class UserRequirement(BaseModel):
    topic: str
    current_level: str
    target_outcome: str
    weekly_hours: int
    budget_inr: int | None = None
    preferred_language: str = "English"


class Creator(BaseModel):
    name: str
    youtube_channel_url: str | None = None
    niche: str
    trust_reason: str
    evidence_urls: list[str] = Field(default_factory=list)


class CourseCandidate(BaseModel):
    title: str
    instructor: str
    provider: str
    url: str
    format: str
    launch_or_update_date: str | None = None
    price: str | None = None
    syllabus_topics: list[str] = Field(default_factory=list)
    creator_connection: str
    evidence_urls: list[str] = Field(default_factory=list)


class ReviewEvidence(BaseModel):
    course_title: str
    source: str
    url: str
    sentiment: str
    positive_themes: list[str] = Field(default_factory=list)
    negative_themes: list[str] = Field(default_factory=list)
    confidence: str


class RankedCourse(BaseModel):
    course_title: str
    score: float = Field(ge=0, le=10)
    goal_relevance: float = Field(ge=0, le=10)
    curriculum_depth: float = Field(ge=0, le=10)
    independent_feedback: float = Field(ge=0, le=10)
    creator_credibility: float = Field(ge=0, le=10)
    recency: float = Field(ge=0, le=10)
    value: float = Field(ge=0, le=10)
    strengths: list[str]
    concerns: list[str]
    decision_reason: str

class CourseURL(BaseModel):
    url: str

class TopicResource(BaseModel):
    topic: str
    video_title: str
    video_url: str
    creator: str
    selection_reason: str


class RoadmapWeek(BaseModel):
    week: int
    topic: str
    learning_goal: str
    primary_course_focus: str
    youtube_resource: TopicResource
    practical_work: str
    completion_criteria: str


class FinalRoadmap(BaseModel):
    title: str
    selected_course: str
    selected_course_url: str
    selected_course_reason: str
    evidence_note: str
    weeks: list[RoadmapWeek]