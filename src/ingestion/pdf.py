"""Native text extraction from PDF documents."""

from io import BytesIO
from uuid import uuid4

from pypdf import PdfReader

from .exceptions import PDFExtractionError, UnsupportedDocumentError
from .models import Document, DocumentInput, ExtractionMethod, Page


class PDFProcessor:
    """Extract native PDF text while preserving the physical page order."""

    def process(self, document_input: DocumentInput) -> Document:
        """Convert a PDF input into a page-aware ingestion document."""
        if document_input.media_type != "application/pdf":
            raise UnsupportedDocumentError(
                f"Unsupported media type for PDF processing: "
                f"{document_input.media_type}"
            )

        try:
            reader = PdfReader(BytesIO(document_input.content))
            pages = [
                Page(
                    page_number=page_number,
                    text=(pdf_page.extract_text() or "").strip(),
                    extraction_method=ExtractionMethod.NATIVE,
                    chunks=[],
                )
                for page_number, pdf_page in enumerate(reader.pages, start=1)
            ]

            return Document(
                document_id=uuid4(),
                filename=document_input.filename,
                media_type=document_input.media_type,
                total_pages=len(pages),
                pages=pages,
            )
        except Exception as exc:
            raise PDFExtractionError("Failed to extract text from PDF") from exc
