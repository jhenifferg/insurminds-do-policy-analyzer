"""Validated, evidence-linked D&O extraction contracts."""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

T = TypeVar("T")


class ExtractionStatus(str, Enum):
    FOUND = "found"
    NOT_FOUND = "not_found"
    AMBIGUOUS = "ambiguous"
    NOT_APPLICABLE = "not_applicable"


class Evidence(BaseModel):
    """Exact source excerpt and its ingestion provenance."""

    model_config = ConfigDict(extra="forbid")

    document_id: str = Field(min_length=1)
    page_number: int = Field(ge=1)
    chunk_id: str = Field(min_length=1)
    quote: str = Field(min_length=1)


class FieldValue(BaseModel, Generic[T]):
    """A value whose uncertainty and supporting evidence are explicit."""

    model_config = ConfigDict(extra="forbid")

    status: ExtractionStatus
    value: T | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    note: str | None = None

    @model_validator(mode="after")
    def validate_status_and_evidence(self) -> "FieldValue[T]":
        if self.status is ExtractionStatus.FOUND:
            if self.value is None or not self.evidence:
                raise ValueError("found fields require a value and source evidence")
        elif self.value is not None:
            raise ValueError("non-found fields cannot contain a value")
        if self.status is ExtractionStatus.AMBIGUOUS and not self.evidence:
            raise ValueError("ambiguous fields require source evidence")
        return self


class MoneyAmount(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: Decimal = Field(ge=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")


class Deductible(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["fixed", "percentage", "mixed"]
    amount: MoneyAmount | None = None
    percentage: Decimal | None = Field(default=None, ge=0, le=100)
    percentage_basis: str | None = None
    description: str | None = None

    @model_validator(mode="after")
    def validate_kind(self) -> "Deductible":
        if self.kind == "fixed" and self.amount is None:
            raise ValueError("fixed deductible requires an amount")
        if self.kind == "percentage" and self.percentage is None:
            raise ValueError("percentage deductible requires a percentage")
        if self.kind == "mixed" and (self.amount is None or self.percentage is None):
            raise ValueError("mixed deductible requires both amount and percentage")
        return self


class CoverageFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    taxonomy_code: str | None = None
    status: Literal["included", "partial", "excluded", "ambiguous"]
    limit: MoneyAmount | None = None
    evidence: list[Evidence] = Field(min_length=1)


class ExclusionFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    category: str | None = None
    trigger: str | None = None
    status: Literal["identified", "ambiguous"] = "identified"
    evidence: list[Evidence] = Field(min_length=1)


class PolicyExtraction(BaseModel):
    """Canonical extraction result for one ingested policy."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"
    document_id: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    insurer: FieldValue[str]
    policy_number: FieldValue[str]
    endorsement: FieldValue[str]
    product: FieldValue[str]
    line_of_business: FieldValue[str]
    issue_date: FieldValue[date]
    insured_name: FieldValue[str]
    insured_cnpj: FieldValue[str]
    effective_start: FieldValue[date]
    effective_end: FieldValue[date]
    retroactivity_date: FieldValue[date]
    extended_reporting_period: FieldValue[str]
    supplementary_period: FieldValue[str]
    run_off: FieldValue[str]
    lmg: FieldValue[MoneyAmount]
    lmi_sublimits: FieldValue[list[CoverageFinding]]
    deductibles: FieldValue[list[Deductible]]
    coverages: FieldValue[list[CoverageFinding]]
    exclusions: FieldValue[list[ExclusionFinding]]
    extensions: FieldValue[list[CoverageFinding]]

    @model_validator(mode="after")
    def validate_policy_period(self) -> "PolicyExtraction":
        if (
            self.effective_start.status is ExtractionStatus.FOUND
            and self.effective_end.status is ExtractionStatus.FOUND
            and self.effective_start.value >= self.effective_end.value
        ):
            raise ValueError("policy end date must be after start date")
        return self


__all__ = [
    "CoverageFinding", "Deductible", "Evidence", "ExclusionFinding",
    "ExtractionStatus", "FieldValue", "MoneyAmount", "PolicyExtraction",
]
