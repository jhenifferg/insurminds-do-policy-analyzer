"""Concrete OCR processing for images and rasterized PDFs."""

from io import BytesIO
from typing import Any, Protocol
from uuid import uuid4

from .classification import InputClassifier, InputType
from .exceptions import OCRProcessingError
from .models import Document, DocumentInput, ExtractionMethod, Page


class TextRecognitionEngine(Protocol):
    """Small replaceable boundary around a text recognition engine."""

    def recognize(self, image: Any) -> str:
        """Recognize text from one raster image."""
        ...


class TesseractTextRecognitionEngine:
    """Adapt pytesseract and the local Tesseract binary to the OCR boundary."""

    def __init__(self, language: str = "por") -> None:
        self.language = language

    def recognize(self, image: Any) -> str:
        try:
            import pytesseract
        except ModuleNotFoundError as exc:
            raise OCRProcessingError(
                "pytesseract is required for OCR; install project dependencies"
            ) from exc

        try:
            text = pytesseract.image_to_string(image, lang=self.language)
        except Exception as exc:
            raise OCRProcessingError(
                "Tesseract OCR is unavailable or failed; install Tesseract "
                "and the requested language data"
            ) from exc

        if not isinstance(text, str):
            raise OCRProcessingError("OCR engine must return text as str")
        return text


class OCRDocumentProcessor:
    """Process supported images and PDFs through a replaceable OCR engine."""

    def __init__(self, engine: TextRecognitionEngine | None = None) -> None:
        self.engine = engine or TesseractTextRecognitionEngine()

    def process(self, document_input: DocumentInput) -> Document:
        """Return an OCR-backed document with one page per source page."""
        input_type = InputClassifier().classify(document_input)
        if not document_input.content:
            raise OCRProcessingError("OCR input content must not be empty")

        try:
            if input_type is InputType.IMAGE:
                texts = [self._process_image(document_input.content)]
            else:
                texts = self._process_pdf(document_input.content)

            pages = [
                Page(
                    page_number=page_number,
                    text=text,
                    extraction_method=ExtractionMethod.OCR,
                    chunks=[],
                )
                for page_number, text in enumerate(texts, start=1)
            ]
            return Document(
                document_id=uuid4(),
                filename=document_input.filename,
                media_type=document_input.media_type,
                total_pages=len(pages),
                pages=pages,
            )
        except OCRProcessingError:
            raise
        except Exception as exc:
            raise OCRProcessingError("OCR processing failed") from exc

    def _process_image(self, content: bytes) -> str:
        image_module = self._load_pillow()
        try:
            with image_module.open(BytesIO(content)) as image:
                image.load()
                return self._recognize(image)
        except OCRProcessingError:
            raise
        except Exception as exc:
            raise OCRProcessingError("Unable to open or OCR image") from exc

    def _process_pdf(self, content: bytes) -> list[str]:
        fitz = self._load_pymupdf()
        image_module = self._load_pillow()
        texts: list[str] = []

        try:
            with fitz.open(stream=content, filetype="pdf") as pdf:
                for pdf_page in pdf:
                    pixmap = pdf_page.get_pixmap(dpi=150, alpha=False)
                    image = image_module.frombytes(
                        "RGB",
                        (pixmap.width, pixmap.height),
                        pixmap.samples,
                    )
                    try:
                        texts.append(self._recognize(image))
                    finally:
                        image.close()
        except OCRProcessingError:
            raise
        except Exception as exc:
            raise OCRProcessingError("Unable to open, rasterize, or OCR PDF") from exc

        if not texts:
            raise OCRProcessingError("PDF does not contain any pages")
        return texts

    def _recognize(self, image: Any) -> str:
        try:
            text = self.engine.recognize(image)
        except OCRProcessingError:
            raise
        except Exception as exc:
            raise OCRProcessingError("OCR engine failed") from exc
        if not isinstance(text, str):
            raise OCRProcessingError("OCR engine must return text as str")
        return text

    @staticmethod
    def _load_pillow() -> Any:
        try:
            from PIL import Image
        except ModuleNotFoundError as exc:
            raise OCRProcessingError(
                "Pillow is required for image OCR processing"
            ) from exc
        return Image

    @staticmethod
    def _load_pymupdf() -> Any:
        try:
            import fitz
        except ModuleNotFoundError as exc:
            raise OCRProcessingError(
                "PyMuPDF is required for PDF OCR processing"
            ) from exc
        return fitz
