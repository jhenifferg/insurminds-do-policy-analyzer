"""Domain contracts for document ingestion."""

from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


def _validate_non_blank(value: str) -> str:
    """Reject empty and whitespace-only textual values."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("must not be empty")
    return value


def _validate_page_text(value: str) -> str:
    """Preserve page text while requiring a string value."""
    if not isinstance(value, str):
        raise ValueError("must be a string")
    return value


def _validate_non_empty(value: str) -> str:
    """Reject empty strings while allowing whitespace-only values."""
    if not isinstance(value, str) or not value:
        raise ValueError("must not be empty")
    return value


class ExtractionMethod(str, Enum):
    """Method used to obtain text from a page."""

    NATIVE = "native"
    OCR = "ocr"


class DocumentInput(BaseModel):
    """Input document received by the ingestion pipeline."""

    filename: str
    media_type: str
    content: bytes

    _filename_not_empty = field_validator("filename", mode="before")(
        _validate_non_blank
    )
    _media_type_not_empty = field_validator("media_type", mode="before")(
        _validate_non_blank
    )

    @field_validator("content")
    @classmethod
    def content_must_not_be_empty(cls, value: bytes) -> bytes:
        if not value:
            raise ValueError("must not be empty")
        return value


class Chunk(BaseModel):
    """A text fragment linked to a document and its source page."""

    chunk_id: str
    document_id: str
    page_number: int = Field(ge=1)
    chunk_index: int = Field(ge=0)
    text: str

    _chunk_id_not_empty = field_validator("chunk_id", mode="before")(
        _validate_non_blank
    )
    _document_id_not_empty = field_validator("document_id", mode="before")(
        _validate_non_blank
    )
    _text_not_empty = field_validator("text", mode="before")(_validate_non_empty)


class Page(BaseModel):
    """Text extracted from one page, with its resulting chunks."""

    page_number: int = Field(ge=1)
    text: str
    extraction_method: ExtractionMethod
    chunks: list[Chunk] = Field(default_factory=list)

    _text_is_valid = field_validator("text", mode="before")(_validate_page_text)


class Document(BaseModel):
    """Ingested document with page-level and chunk-level traceability."""

    document_id: UUID
    filename: str
    media_type: str
    total_pages: int = Field(ge=1)
    pages: list[Page] = Field(min_length=1)

    _filename_not_empty = field_validator("filename", mode="before")(
        _validate_non_blank
    )
    _media_type_not_empty = field_validator("media_type", mode="before")(
        _validate_non_blank
    )

    @model_validator(mode="after")
    def validate_pages(self) -> "Document":
        if self.total_pages != len(self.pages):
            raise ValueError("total_pages must match the number of pages")

        page_numbers = [page.page_number for page in self.pages]
        if len(page_numbers) != len(set(page_numbers)):
            raise ValueError("page numbers must be unique")

        return self
