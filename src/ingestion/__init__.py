"""Public contracts and exceptions for document ingestion."""

from .exceptions import (
    DocumentIngestionError,
    DocumentProcessingError,
    InvalidDocumentError,
    OCRProcessingError,
    PDFExtractionError,
    UnsupportedDocumentError,
)
from .cleaning import TextCleaner
from .chunking import Chunker
from .classification import InputClassifier, InputType
from .interfaces import OCRProcessor
from .models import Chunk, Document, DocumentInput, ExtractionMethod, Page
from .ocr import OCRDocumentProcessor
from .pdf import PDFProcessor
from .pipeline import DocumentIngestionPipeline

__all__ = [
    "Chunk",
    "Chunker",
    "Document",
    "DocumentIngestionError",
    "DocumentInput",
    "DocumentIngestionPipeline",
    "DocumentProcessingError",
    "ExtractionMethod",
    "InvalidDocumentError",
    "InputClassifier",
    "InputType",
    "OCRProcessingError",
    "OCRDocumentProcessor",
    "OCRProcessor",
    "PDFExtractionError",
    "Page",
    "PDFProcessor",
    "TextCleaner",
    "UnsupportedDocumentError",
]
