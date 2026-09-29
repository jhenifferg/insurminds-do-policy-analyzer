from io import BytesIO
from types import SimpleNamespace
from uuid import UUID

import pytest
from PIL import Image
from pypdf import PdfWriter

from src.ingestion import (
    DocumentInput,
    ExtractionMethod,
    OCRDocumentProcessor,
    OCRProcessingError,
    UnsupportedDocumentError,
)


class FakeTextRecognitionEngine:
    def __init__(self, texts: list[str]) -> None:
        self.texts = iter(texts)
        self.calls = 0

    def recognize(self, image: object) -> str:
        self.calls += 1
        return next(self.texts)


def make_image(media_type: str, image_format: str) -> DocumentInput:
    output = BytesIO()
    Image.new("RGB", (8, 8), color="white").save(output, format=image_format)
    return DocumentInput(
        filename=f"document.{image_format.lower()}",
        media_type=media_type,
        content=output.getvalue(),
    )


def make_pdf(page_count: int) -> bytes:
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=100, height=100)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def make_pdf_input(content: bytes) -> DocumentInput:
    return DocumentInput(
        filename="scanned.pdf",
        media_type="application/pdf",
        content=content,
    )


@pytest.mark.parametrize(
    ("media_type", "image_format"),
    [("image/jpeg", "JPEG"), ("image/png", "PNG")],
)
def test_processes_image_as_one_ocr_page(media_type: str, image_format: str) -> None:
    engine = FakeTextRecognitionEngine(["texto reconhecido"])
    document = OCRDocumentProcessor(engine=engine).process(
        make_image(media_type, image_format)
    )

    assert document.total_pages == 1
    assert len(document.pages) == 1
    assert document.pages[0].page_number == 1
    assert document.pages[0].extraction_method is ExtractionMethod.OCR
    assert document.pages[0].text == "texto reconhecido"
    assert document.pages[0].chunks == []
    assert document.filename == f"document.{image_format.lower()}"
    assert document.media_type == media_type
    assert isinstance(document.document_id, UUID)
    assert engine.calls == 1


def test_processes_pdf_page_by_page_with_ocr() -> None:
    engine = FakeTextRecognitionEngine(["página 1", "página 2", "página 3"])
    document = OCRDocumentProcessor(engine=engine).process(
        make_pdf_input(make_pdf(3))
    )

    assert document.total_pages == 3
    assert [page.page_number for page in document.pages] == [1, 2, 3]
    assert [page.text for page in document.pages] == [
        "página 1",
        "página 2",
        "página 3",
    ]
    assert all(
        page.extraction_method is ExtractionMethod.OCR for page in document.pages
    )
    assert all(page.chunks == [] for page in document.pages)
    assert engine.calls == 3


def test_each_processing_generates_a_new_document_id() -> None:
    content = make_image("image/png", "PNG")
    first = OCRDocumentProcessor(engine=FakeTextRecognitionEngine(["one"])).process(
        content
    )
    second = OCRDocumentProcessor(
        engine=FakeTextRecognitionEngine(["two"])
    ).process(content)

    assert isinstance(first.document_id, UUID)
    assert isinstance(second.document_id, UUID)
    assert first.document_id != second.document_id


@pytest.mark.parametrize("media_type", ["text/plain", "image/gif"])
def test_rejects_unsupported_media_type(media_type: str) -> None:
    document_input = DocumentInput(
        filename="document.bin",
        media_type=media_type,
        content=b"content",
    )

    with pytest.raises(UnsupportedDocumentError):
        OCRDocumentProcessor(engine=FakeTextRecognitionEngine(["text"])).process(
            document_input
        )


def test_invalid_image_raises_ocr_processing_error() -> None:
    document_input = DocumentInput(
        filename="invalid.png",
        media_type="image/png",
        content=b"not an image",
    )

    with pytest.raises(OCRProcessingError) as error:
        OCRDocumentProcessor(engine=FakeTextRecognitionEngine(["text"])).process(
            document_input
        )

    assert error.value.__cause__ is not None


def test_invalid_pdf_raises_ocr_processing_error() -> None:
    document_input = DocumentInput(
        filename="invalid.pdf",
        media_type="application/pdf",
        content=b"not a pdf",
    )

    with pytest.raises(OCRProcessingError) as error:
        OCRDocumentProcessor(engine=FakeTextRecognitionEngine(["text"])).process(
            document_input
        )

    assert error.value.__cause__ is not None


def test_empty_content_raises_ocr_processing_error() -> None:
    document_input = DocumentInput.model_construct(
        filename="empty.png",
        media_type="image/png",
        content=b"",
    )

    with pytest.raises(OCRProcessingError):
        OCRDocumentProcessor(engine=FakeTextRecognitionEngine(["text"])).process(
            document_input
        )


def test_missing_pytesseract_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(__import__("sys").modules, "pytesseract", None)

    with pytest.raises(OCRProcessingError, match="pytesseract"):
        from src.ingestion.ocr import TesseractTextRecognitionEngine

        TesseractTextRecognitionEngine().recognize(SimpleNamespace())
