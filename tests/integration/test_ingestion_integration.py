import shutil
from uuid import UUID

import pytest

from src.ingestion import (
    Chunker,
    DocumentIngestionPipeline,
    DocumentInput,
    ExtractionMethod,
    OCRDocumentProcessor,
    OCRProcessingError,
    PDFExtractionError,
)

from .conftest import make_scanned_pdf, make_text_image, make_text_pdf


TESSERACT_AVAILABLE = shutil.which("tesseract") is not None
requires_tesseract = pytest.mark.skipif(
    not TESSERACT_AVAILABLE,
    reason="Tesseract indisponível no ambiente",
)


def test_textual_pdf_runs_through_real_pipeline() -> None:
    content = make_text_pdf(
        [
            "POLIZA DE TESTE | Segurado: Empresa Exemplo | Limite: R$ 1000000",
            "VIGENCIA: 01/01/2026 a 31/12/2026 | PAGINA DOIS",
        ]
    )
    document_input = DocumentInput(
        filename="policy.pdf",
        media_type="application/pdf",
        content=content,
    )

    document = DocumentIngestionPipeline(
        chunker=Chunker(max_chunk_size=25)
    ).process(document_input)

    assert isinstance(document.document_id, UUID)
    assert document.total_pages == 2
    assert [page.page_number for page in document.pages] == [1, 2]
    assert all(
        page.extraction_method is ExtractionMethod.NATIVE for page in document.pages
    )
    assert "POLIZA DE TESTE" in document.pages[0].text
    assert "VIGENCIA" in document.pages[1].text
    assert all(page.text == page.text.strip() for page in document.pages)
    assert all(len(page.chunks) > 1 for page in document.pages)

    for page in document.pages:
        assert all(chunk.page_number == page.page_number for chunk in page.chunks)
        assert all(
            chunk.document_id == str(document.document_id) for chunk in page.chunks
        )
        assert [chunk.chunk_index for chunk in page.chunks] == list(
            range(len(page.chunks))
        )
        assert all(
            chunk.chunk_id
            == f"{document.document_id}:page-{page.page_number}:"
            f"chunk-{chunk.chunk_index}"
            for chunk in page.chunks
        )


@requires_tesseract
def test_real_image_runs_through_pipeline_with_ocr() -> None:
    content = make_text_image(
        ["APOLICE D&O", "LIMITE: R$ 2000000", "FRANQUIA: R$ 50000"]
    )
    document_input = DocumentInput(
        filename="policy.png",
        media_type="image/png",
        content=content,
    )

    document = DocumentIngestionPipeline().process(document_input)

    assert isinstance(document.document_id, UUID)
    assert document.total_pages == 1
    assert document.pages[0].extraction_method is ExtractionMethod.OCR
    recognized_text = document.pages[0].text.upper()
    assert "APOLICE" in recognized_text
    assert "LIMITE" in recognized_text
    assert "FRANQUIA" in recognized_text
    assert document.pages[0].text == document.pages[0].text.strip()
    assert document.pages[0].chunks
    assert all(
        chunk.document_id == str(document.document_id)
        for chunk in document.pages[0].chunks
    )


@requires_tesseract
def test_scanned_pdf_runs_through_explicit_ocr_processor() -> None:
    document_input = DocumentInput(
        filename="scanned-policy.pdf",
        media_type="application/pdf",
        content=make_scanned_pdf(["PDF ESCANEADO", "LIMITE: R$ 3000000"]),
    )

    document = OCRDocumentProcessor().process(document_input)

    assert isinstance(document.document_id, UUID)
    assert document.total_pages == 1
    assert document.pages[0].page_number == 1
    assert document.pages[0].extraction_method is ExtractionMethod.OCR
    recognized_text = document.pages[0].text.upper()
    assert "ESCANEADO" in recognized_text
    assert "LIMITE" in recognized_text


@requires_tesseract
def test_scanned_pdf_falls_back_to_ocr_in_real_pipeline() -> None:
    document_input = DocumentInput(
        filename="scanned-policy.pdf",
        media_type="application/pdf",
        content=make_scanned_pdf(["PDF ESCANEADO", "LIMITE: R$ 3000000"]),
    )

    document = DocumentIngestionPipeline().process(document_input)

    assert isinstance(document.document_id, UUID)
    assert document.total_pages == 1
    assert document.pages[0].extraction_method is ExtractionMethod.OCR
    assert document.pages[0].chunks
    recognized_text = document.pages[0].text.upper()
    assert "ESCANEADO" in recognized_text
    assert all(
        chunk.document_id == str(document.document_id)
        for chunk in document.pages[0].chunks
    )


@pytest.mark.skipif(
    TESSERACT_AVAILABLE,
    reason="Teste específico para ausência do executável Tesseract",
)
def test_missing_tesseract_is_reported_without_masking() -> None:
    document_input = DocumentInput(
        filename="policy.png",
        media_type="image/png",
        content=make_text_image(["OCR DEPENDENCY TEST"]),
    )

    with pytest.raises(OCRProcessingError, match="Tesseract"):
        OCRDocumentProcessor().process(document_input)


def test_invalid_pdf_raises_real_extraction_error() -> None:
    document_input = DocumentInput(
        filename="invalid.pdf",
        media_type="application/pdf",
        content=b"not a PDF",
    )

    with pytest.raises(PDFExtractionError):
        DocumentIngestionPipeline().process(document_input)


def test_invalid_image_raises_real_ocr_error() -> None:
    document_input = DocumentInput(
        filename="invalid.png",
        media_type="image/png",
        content=b"not an image",
    )

    with pytest.raises(OCRProcessingError):
        OCRDocumentProcessor().process(document_input)
