from __future__ import annotations

from pydantic import Field, model_validator

from app.core.schemas import CamelModel


class ResumeParseRequest(CamelModel):
    resume_text: str = Field(min_length=20, max_length=100_000)


class ProjectExperience(CamelModel):
    name: str
    summary: str
    technologies: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class ResumeParseResult(CamelModel):
    name: str | None = None
    school: str | None = None
    major: str | None = None
    graduation_time: str | None = None
    skills: list[str] = Field(default_factory=list)
    projects: list[ProjectExperience] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_meaningful_content(self) -> "ResumeParseResult":
        scalar_values = (self.name, self.school, self.major, self.graduation_time)
        if (
            any(value and value.strip() for value in scalar_values)
            or self.skills
            or self.projects
        ):
            return self
        raise ValueError("resume parse result must contain at least one extracted field")


class ScreeningRequest(CamelModel):
    resume_text: str = Field(min_length=20, max_length=100_000)
    job_description: str = Field(min_length=20, max_length=50_000)


class ScreeningResult(CamelModel):
    match_score: int = Field(ge=0, le=100)
    recommendation: str
    confidence: float = Field(ge=0, le=1)
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    interview_focus: list[str] = Field(default_factory=list)
    final_comment: str


class InterviewKitRequest(CamelModel):
    resume_text: str = Field(min_length=20, max_length=100_000)
    job_description: str = Field(min_length=20, max_length=50_000)
    screening_risks: list[str] = Field(default_factory=list, max_length=30)


class InterviewQuestion(CamelModel):
    type: str
    question: str
    purpose: str


class InterviewKitResult(CamelModel):
    questions: list[InterviewQuestion] = Field(min_length=1, max_length=30)
