from src.ingestion import (
    DocumentIngestionError,
    DocumentProcessingError,
    InvalidDocumentError,
    OCRProcessingError,
    PDFExtractionError,
    UnsupportedDocumentError,
)


def test_all_ingestion_exceptions_share_the_base_class() -> None:
    exception_types = (
        UnsupportedDocumentError,
        InvalidDocumentError,
        DocumentProcessingError,
        PDFExtractionError,
        OCRProcessingError,
    )

    assert all(
        issubclass(exception_type, DocumentIngestionError)
        for exception_type in exception_types
    )


def test_extraction_errors_are_processing_errors() -> None:
    assert issubclass(PDFExtractionError, DocumentProcessingError)
    assert issubclass(OCRProcessingError, DocumentProcessingError)
