"""Orchestration of the document ingestion components."""

from .classification import InputClassifier, InputType
from .cleaning import TextCleaner
from .chunking import Chunker
from .interfaces import OCRProcessor
from .models import Document, DocumentInput
from .ocr import OCRDocumentProcessor
from .pdf import PDFProcessor


class DocumentIngestionPipeline:
    """Coordinate classification, processing, cleaning, and chunking."""

    def __init__(
        self,
        classifier: InputClassifier | None = None,
        pdf_processor: PDFProcessor | None = None,
        ocr_processor: OCRProcessor | None = None,
        cleaner: TextCleaner | None = None,
        chunker: Chunker | None = None,
    ) -> None:
        self.classifier = classifier if classifier is not None else InputClassifier()
        self.pdf_processor = (
            pdf_processor if pdf_processor is not None else PDFProcessor()
        )
        self.ocr_processor = (
            ocr_processor
            if ocr_processor is not None
            else OCRDocumentProcessor()
        )
        self.cleaner = cleaner if cleaner is not None else TextCleaner()
        self.chunker = chunker if chunker is not None else Chunker()

    def process(self, document_input: DocumentInput) -> Document:
        """Process one input while preserving the processor's document identity."""
        input_type = self.classifier.classify(document_input)

        if input_type is InputType.PDF:
            document = self.pdf_processor.process(document_input)
            if not any(page.text.strip() for page in document.pages):
                document = self.ocr_processor.process(document_input)
        elif input_type is InputType.IMAGE:
            document = self.ocr_processor.process(document_input)
        else:
            raise ValueError(f"Unsupported classified input type: {input_type}")

        for page in document.pages:
            page.text = self.cleaner.clean(page.text)
            page.chunks = self.chunker.chunk_page(document.document_id, page)

        return document
