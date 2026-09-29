"""Protocols defining boundaries for future ingestion implementations."""

from typing import Protocol

from .models import Document, DocumentInput


class OCRProcessor(Protocol):
    """Contract for OCR implementations processing one document input."""

    def process(self, document: DocumentInput) -> Document:
        """Process a PDF or image with OCR and return a page-aware document."""
        ...
