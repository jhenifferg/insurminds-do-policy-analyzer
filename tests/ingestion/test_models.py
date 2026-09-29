import pytest
from pydantic import ValidationError
from uuid import UUID

from src.ingestion import Chunk, Document, DocumentInput, ExtractionMethod, Page


DOCUMENT_ID = UUID("12345678-1234-5678-1234-567812345678")


def make_page(page_number: int = 1) -> Page:
    return Page(
        page_number=page_number,
        text=f"Page {page_number} text",
        extraction_method=ExtractionMethod.NATIVE,
    )


def test_document_input_accepts_valid_document() -> None:
    document = DocumentInput(
        filename="policy.pdf",
        media_type="application/pdf",
        content=b"pdf-content",
    )

    assert document.filename == "policy.pdf"
    assert document.media_type == "application/pdf"
    assert document.content == b"pdf-content"


def test_document_input_requires_all_fields() -> None:
    with pytest.raises(ValidationError):
        DocumentInput()


@pytest.mark.parametrize(
    ("field", "value"),
    [("filename", ""), ("filename", "  "), ("media_type", ""), ("media_type", "  ")],
)
def test_document_input_rejects_empty_text_fields(field: str, value: str) -> None:
    data = {
        "filename": "policy.pdf",
        "media_type": "application/pdf",
        "content": b"pdf-content",
    }
    data[field] = value

    with pytest.raises(ValidationError):
        DocumentInput(**data)


def test_document_input_rejects_empty_content() -> None:
    with pytest.raises(ValidationError):
        DocumentInput(
            filename="policy.pdf",
            media_type="application/pdf",
            content=b"",
        )


def test_chunk_accepts_valid_chunk() -> None:
    chunk = Chunk(
        chunk_id="chunk-1",
        document_id="document-1",
        page_number=2,
        chunk_index=0,
        text="Coverage text",
    )

    assert chunk.page_number == 2
    assert chunk.chunk_index == 0


def test_chunk_requires_identifiers_and_text() -> None:
    with pytest.raises(ValidationError):
        Chunk(
            chunk_id="",
            document_id="document-1",
            page_number=1,
            chunk_index=0,
            text="text",
        )

    with pytest.raises(ValidationError):
        Chunk(
            chunk_id="chunk-1",
            document_id="document-1",
            page_number=1,
            chunk_index=0,
            text="",
        )


@pytest.mark.parametrize("text", ["   ", "\n\n", "\t"])
def test_chunk_accepts_whitespace_only_text(text: str) -> None:
    chunk = Chunk(
        chunk_id="chunk-1",
        document_id="document-1",
        page_number=1,
        chunk_index=0,
        text=text,
    )

    assert chunk.text == text


@pytest.mark.parametrize("model", [Chunk, Page])
def test_chunk_and_page_require_all_fields(model: type[Chunk] | type[Page]) -> None:
    with pytest.raises(ValidationError):
        model()


@pytest.mark.parametrize(
    ("page_number", "chunk_index"),
    [(0, 0), (-1, 0), (1, -1)],
)
def test_chunk_rejects_invalid_numeric_limits(page_number: int, chunk_index: int) -> None:
    with pytest.raises(ValidationError):
        Chunk(
            chunk_id="chunk-1",
            document_id=DOCUMENT_ID,
            page_number=page_number,
            chunk_index=chunk_index,
            text="text",
        )


def test_page_accepts_valid_page_and_defaults_chunks() -> None:
    page = make_page()

    assert page.page_number == 1
    assert page.extraction_method is ExtractionMethod.NATIVE
    assert page.chunks == []


def test_page_rejects_invalid_page_number_and_method() -> None:
    with pytest.raises(ValidationError):
        Page(page_number=0, text="text", extraction_method=ExtractionMethod.OCR)

    with pytest.raises(ValidationError):
        Page(page_number=1, text=123, extraction_method=ExtractionMethod.OCR)

    with pytest.raises(ValidationError):
        Page(page_number=1, text="text", extraction_method="manual")


def test_page_accepts_empty_text() -> None:
    page = Page(
        page_number=1,
        text="",
        extraction_method=ExtractionMethod.NATIVE,
        chunks=[],
    )

    assert page.text == ""


@pytest.mark.parametrize("text", ["   ", "\n\n", "\t", "texto"])
def test_page_preserves_empty_and_whitespace_text(text: str) -> None:
    page = Page(
        page_number=1,
        text=text,
        extraction_method=ExtractionMethod.NATIVE,
    )

    assert page.text == text


def test_page_chunks_default_is_independent_between_instances() -> None:
    first_page = make_page()
    second_page = make_page()
    chunk = Chunk(
        chunk_id="chunk-1",
        document_id="document-1",
        page_number=1,
        chunk_index=0,
        text="text",
    )

    first_page.chunks.append(chunk)

    assert first_page.chunks == [chunk]
    assert second_page.chunks == []
    assert first_page.chunks is not second_page.chunks


def test_document_accepts_valid_pages_and_preserves_original_numbers() -> None:
    document = Document(
        document_id=DOCUMENT_ID,
        filename="policy.pdf",
        media_type="application/pdf",
        total_pages=2,
        pages=[make_page(3), make_page(7)],
    )

    assert isinstance(document.document_id, UUID)
    assert document.total_pages == 2
    assert [page.page_number for page in document.pages] == [3, 7]


def test_document_requires_identifiers_metadata_and_pages() -> None:
    with pytest.raises(ValidationError):
        Document()

    with pytest.raises(ValidationError):
        Document(
            document_id=DOCUMENT_ID,
            filename="policy.pdf",
            media_type="application/pdf",
            total_pages=1,
            pages=[],
        )


def test_document_rejects_empty_text_metadata() -> None:
    with pytest.raises(ValidationError):
        Document(
            document_id=" ",
            filename="policy.pdf",
            media_type="application/pdf",
            total_pages=1,
            pages=[make_page()],
        )


@pytest.mark.parametrize("total_pages", [0, -1])
def test_document_rejects_invalid_total_pages(total_pages: int) -> None:
    with pytest.raises(ValidationError):
        Document(
            document_id=DOCUMENT_ID,
            filename="policy.pdf",
            media_type="application/pdf",
            total_pages=total_pages,
            pages=[make_page()],
        )


def test_document_rejects_inconsistent_page_count() -> None:
    with pytest.raises(ValidationError):
        Document(
            document_id=DOCUMENT_ID,
            filename="policy.pdf",
            media_type="application/pdf",
            total_pages=2,
            pages=[make_page()],
        )


def test_document_rejects_duplicate_page_numbers() -> None:
    with pytest.raises(ValidationError):
        Document(
            document_id=DOCUMENT_ID,
            filename="policy.pdf",
            media_type="application/pdf",
            total_pages=2,
            pages=[make_page(1), make_page(1)],
        )
