"""Exceptions raised by the document ingestion pipeline."""


class DocumentIngestionError(Exception):
    """Base exception for document ingestion failures."""


class UnsupportedDocumentError(DocumentIngestionError):
    """Raised when a document format is not supported."""


class InvalidDocumentError(DocumentIngestionError):
    """Raised when a document is malformed or fails input validation."""


class DocumentProcessingError(DocumentIngestionError):
    """Raised when processing a supported document fails."""


class PDFExtractionError(DocumentProcessingError):
    """Raised when native PDF text extraction fails."""


class OCRProcessingError(DocumentProcessingError):
    """Raised when OCR processing fails."""
