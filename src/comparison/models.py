"""Structured outputs for deterministic policy comparisons."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from src.extraction.models import Evidence


class DifferenceKind(str, Enum):
    HIGHER = "higher"
    LOWER = "lower"
    EQUAL = "equal"
    DIFFERENT = "different"
    NEEDS_REVIEW = "needs_review"
    NOT_COMPARABLE = "not_comparable"


class ComparisonRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criterion: str = Field(min_length=1)
    policy_a: str
    policy_b: str
    difference: DifferenceKind
    explanation: str
    evidence_policy_a: list[Evidence] = Field(default_factory=list)
    evidence_policy_b: list[Evidence] = Field(default_factory=list)


class ComparisonReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_a_document_id: str
    policy_a_name: str
    policy_b_document_id: str
    policy_b_name: str
    rows: list[ComparisonRow]


__all__ = ["ComparisonReport", "ComparisonRow", "DifferenceKind"]
