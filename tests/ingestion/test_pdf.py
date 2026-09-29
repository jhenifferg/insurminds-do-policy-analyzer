from io import BytesIO
from uuid import UUID

import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from src.ingestion import (
    DocumentInput,
    ExtractionMethod,
    PDFExtractionError,
    PDFProcessor,
    UnsupportedDocumentError,
)


def create_pdf(page_texts: list[str | None]) -> bytes:
    """Create a small in-memory PDF with optional text on each page."""
    writer = PdfWriter()

    for page_text in page_texts:
        page = writer.add_blank_page(width=612, height=792)
        if page_text:
            font = DictionaryObject(
                {
                    NameObject("/Type"): NameObject("/Font"),
                    NameObject("/Subtype"): NameObject("/Type1"),
                    NameObject("/BaseFont"): NameObject("/Helvetica"),
                }
            )
            page[NameObject("/Resources")] = DictionaryObject(
                {
                    NameObject("/Font"): DictionaryObject(
                        {NameObject("/F1"): font}
                    )
                }
            )
            content = DecodedStreamObject()
            content.set_data(
                f"BT /F1 12 Tf 72 720 Td ({page_text}) Tj ET".encode("latin-1")
            )
            page[NameObject("/Contents")] = writer._add_object(content)

    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def make_input(content: bytes, **kwargs: str) -> DocumentInput:
    return DocumentInput(
        filename=kwargs.get("filename", "policy.pdf"),
        media_type=kwargs.get("media_type", "application/pdf"),
        content=content,
    )


def test_processes_single_page_pdf() -> None:
    document = PDFProcessor().process(make_input(create_pdf(["APOLICE TESTE"])))

    assert document.total_pages == 1
    assert len(document.pages) == 1
    assert document.pages[0].page_number == 1
    assert "APOLICE TESTE" in document.pages[0].text
    assert document.pages[0].extraction_method is ExtractionMethod.NATIVE
    assert document.pages[0].chunks == []


def test_processes_multiple_pages_in_original_order() -> None:
    document = PDFProcessor().process(
        make_input(create_pdf(["APOLICE TESTE", "COBERTURAS", "EXCLUSOES"]))
    )

    assert document.total_pages == 3
    assert [page.page_number for page in document.pages] == [1, 2, 3]
    assert [page.text for page in document.pages] == [
        "APOLICE TESTE",
        "COBERTURAS",
        "EXCLUSOES",
    ]


def test_generates_new_document_id_for_each_processing() -> None:
    pdf = create_pdf(["APOLICE TESTE"])

    first_document = PDFProcessor().process(make_input(pdf))
    second_document = PDFProcessor().process(make_input(pdf))

    assert isinstance(first_document.document_id, UUID)
    assert isinstance(second_document.document_id, UUID)
    assert first_document.document_id != second_document.document_id


def test_preserves_filename_and_media_type() -> None:
    document = PDFProcessor().process(
        make_input(
            create_pdf(["APOLICE TESTE"]),
            filename="original-policy.pdf",
            media_type="application/pdf",
        )
    )

    assert document.filename == "original-policy.pdf"
    assert document.media_type == "application/pdf"


def test_rejects_unsupported_media_type() -> None:
    document_input = make_input(
        create_pdf(["APOLICE TESTE"]),
        media_type="image/png",
    )

    with pytest.raises(UnsupportedDocumentError):
        PDFProcessor().process(document_input)


def test_maps_invalid_pdf_to_pdf_extraction_error() -> None:
    with pytest.raises(PDFExtractionError) as error:
        PDFProcessor().process(make_input(b"not a valid PDF"))

    assert error.value.__cause__ is not None


def test_preserves_page_without_extractable_text() -> None:
    document = PDFProcessor().process(
        make_input(create_pdf(["APOLICE TESTE", None]))
    )

    empty_page = document.pages[1]
    assert document.total_pages == 2
    assert empty_page.page_number == 2
    assert empty_page.text == ""
    assert empty_page.extraction_method is ExtractionMethod.NATIVE
    assert empty_page.chunks == []
