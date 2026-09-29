from uuid import UUID

import pytest

from src.ingestion import (
    Chunk,
    Chunker,
    Document,
    DocumentIngestionPipeline,
    DocumentInput,
    ExtractionMethod,
    InputType,
    OCRProcessingError,
    Page,
)


DOCUMENT_ID = UUID("12345678-1234-5678-1234-567812345678")


def make_input(media_type: str) -> DocumentInput:
    return DocumentInput(
        filename="policy.pdf" if media_type == "application/pdf" else "page.png",
        media_type=media_type,
        content=b"document-content",
    )


def make_document(
    *texts: str,
    document_id: UUID = DOCUMENT_ID,
    extraction_method: ExtractionMethod = ExtractionMethod.NATIVE,
) -> Document:
    return Document(
        document_id=document_id,
        filename="processed-document",
        media_type="application/pdf",
        total_pages=len(texts),
        pages=[
            Page(
                page_number=page_number,
                text=text,
                extraction_method=extraction_method,
            )
            for page_number, text in enumerate(texts, start=1)
        ],
    )


class FakeClassifier:
    def __init__(
        self,
        input_type: InputType,
        events: list[object],
        error: BaseException | None = None,
    ) -> None:
        self.input_type = input_type
        self.events = events
        self.error = error

    def classify(self, document_input: DocumentInput) -> InputType:
        self.events.append("classification")
        if self.error is not None:
            raise self.error
        return self.input_type


class FakeProcessor:
    def __init__(
        self,
        name: str,
        document: Document,
        events: list[object],
        error: BaseException | None = None,
    ) -> None:
        self.name = name
        self.document = document
        self.events = events
        self.error = error
        self.calls = 0

    def process(self, document_input: DocumentInput) -> Document:
        self.calls += 1
        self.events.append(self.name)
        if self.error is not None:
            raise self.error
        return self.document


class FakeCleaner:
    def __init__(
        self,
        events: list[object],
        replacements: dict[str, str] | None = None,
        error: BaseException | None = None,
    ) -> None:
        self.events = events
        self.replacements = replacements or {}
        self.error = error

    def clean(self, text: str) -> str:
        self.events.append(("cleaning", text))
        if self.error is not None:
            raise self.error
        return self.replacements.get(text, text)


class FakeChunker:
    def __init__(
        self,
        events: list[object],
        error: BaseException | None = None,
    ) -> None:
        self.events = events
        self.error = error
        self.calls: list[tuple[UUID, int, str]] = []

    def chunk_page(self, document_id: UUID, page: Page) -> list[Chunk]:
        self.events.append(("chunking", page.page_number, page.text))
        self.calls.append((document_id, page.page_number, page.text))
        if self.error is not None:
            raise self.error
        if page.text == "":
            return []
        return [
            Chunk(
                chunk_id=f"chunk-{page.page_number}",
                document_id=str(document_id),
                page_number=page.page_number,
                chunk_index=0,
                text=page.text,
            )
        ]


def make_pipeline(
    input_type: InputType,
    document: Document,
    events: list[object],
    *,
    replacements: dict[str, str] | None = None,
    ocr_document: Document | None = None,
    classifier_error: BaseException | None = None,
    pdf_error: BaseException | None = None,
    ocr_error: BaseException | None = None,
    cleaner_error: BaseException | None = None,
    chunker_error: BaseException | None = None,
) -> tuple[DocumentIngestionPipeline, FakeProcessor, FakeProcessor, FakeCleaner, FakeChunker]:
    classifier = FakeClassifier(input_type, events, classifier_error)
    pdf_processor = FakeProcessor("pdf-processing", document, events, pdf_error)
    ocr_processor = FakeProcessor(
        "ocr-processing",
        ocr_document if ocr_document is not None else document,
        events,
        ocr_error,
    )
    cleaner = FakeCleaner(events, replacements, cleaner_error)
    chunker = FakeChunker(events, chunker_error)
    pipeline = DocumentIngestionPipeline(
        classifier=classifier,
        pdf_processor=pdf_processor,
        ocr_processor=ocr_processor,
        cleaner=cleaner,
        chunker=chunker,
    )
    return pipeline, pdf_processor, ocr_processor, cleaner, chunker


def test_pdf_uses_pdf_processor_and_not_ocr() -> None:
    events: list[object] = []
    document = make_document("raw PDF text")
    pipeline, pdf_processor, ocr_processor, _, _ = make_pipeline(
        InputType.PDF,
        document,
        events,
        replacements={"raw PDF text": "clean PDF text"},
    )

    result = pipeline.process(make_input("application/pdf"))

    assert result is document
    assert events == [
        "classification",
        "pdf-processing",
        ("cleaning", "raw PDF text"),
        ("chunking", 1, "clean PDF text"),
    ]
    assert pdf_processor.calls == 1
    assert ocr_processor.calls == 0
    assert result.pages[0].chunks[0].text == "clean PDF text"


def test_pdf_without_useful_text_falls_back_to_ocr() -> None:
    events: list[object] = []
    native_document = make_document("", "   ", "\n\n", "\t")
    ocr_document_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    ocr_document = make_document(
        "OCR result",
        document_id=ocr_document_id,
        extraction_method=ExtractionMethod.OCR,
    )
    pipeline, pdf_processor, ocr_processor, _, chunker = make_pipeline(
        InputType.PDF,
        native_document,
        events,
        ocr_document=ocr_document,
        replacements={"OCR result": "clean OCR result"},
    )

    result = pipeline.process(make_input("application/pdf"))

    assert result is ocr_document
    assert result is not native_document
    assert result.document_id == ocr_document_id
    assert pdf_processor.calls == 1
    assert ocr_processor.calls == 1
    assert events == [
        "classification",
        "pdf-processing",
        "ocr-processing",
        ("cleaning", "OCR result"),
        ("chunking", 1, "clean OCR result"),
    ]
    assert chunker.calls == [(ocr_document_id, 1, "clean OCR result")]
    assert [page.text for page in native_document.pages] == ["", "   ", "\n\n", "\t"]
    for page in result.pages:
        for chunk in page.chunks:
            assert chunk.document_id == str(result.document_id)
            assert chunk.page_number == page.page_number


def test_partially_textual_pdf_keeps_native_document_without_ocr() -> None:
    events: list[object] = []
    native_document = make_document("texto nativo", "")
    ocr_document = make_document(
        "OCR should not run",
        document_id=UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        extraction_method=ExtractionMethod.OCR,
    )
    pipeline, _, ocr_processor, _, _ = make_pipeline(
        InputType.PDF,
        native_document,
        events,
        ocr_document=ocr_document,
        replacements={"texto nativo": "texto limpo"},
    )

    result = pipeline.process(make_input("application/pdf"))

    assert result is native_document
    assert ocr_processor.calls == 0
    assert [page.text for page in result.pages] == ["texto limpo", ""]
    assert events == [
        "classification",
        "pdf-processing",
        ("cleaning", "texto nativo"),
        ("chunking", 1, "texto limpo"),
        ("cleaning", ""),
        ("chunking", 2, ""),
    ]


def test_image_uses_ocr_processor_and_not_pdf() -> None:
    events: list[object] = []
    document = make_document("raw OCR text")
    pipeline, pdf_processor, ocr_processor, _, _ = make_pipeline(
        InputType.IMAGE,
        document,
        events,
        replacements={"raw OCR text": "clean OCR text"},
    )

    result = pipeline.process(make_input("image/png"))

    assert result is document
    assert events == [
        "classification",
        "ocr-processing",
        ("cleaning", "raw OCR text"),
        ("chunking", 1, "clean OCR text"),
    ]
    assert pdf_processor.calls == 0
    assert ocr_processor.calls == 1
    chunk = result.pages[0].chunks[0]
    assert result.pages[0].page_number == 1
    assert chunk.document_id == str(result.document_id)
    assert chunk.page_number == 1
    assert chunk.chunk_index == 0
    assert chunk.chunk_id == "chunk-1"


def test_multi_page_chunks_preserve_complete_provenance() -> None:
    events: list[object] = []
    document = make_document("abcdefgh", "12345678")
    classifier = FakeClassifier(InputType.PDF, events)
    pdf_processor = FakeProcessor("pdf-processing", document, events)
    ocr_processor = FakeProcessor("ocr-processing", document, events)
    cleaner = FakeCleaner(events)
    pipeline = DocumentIngestionPipeline(
        classifier=classifier,
        pdf_processor=pdf_processor,
        ocr_processor=ocr_processor,
        cleaner=cleaner,
        chunker=Chunker(max_chunk_size=3),
    )

    result = pipeline.process(make_input("application/pdf"))

    assert [len(page.chunks) for page in result.pages] == [3, 3]
    for page in result.pages:
        assert [chunk.page_number for chunk in page.chunks] == [
            page.page_number
        ] * len(page.chunks)
        assert [chunk.chunk_index for chunk in page.chunks] == list(
            range(len(page.chunks))
        )
        for chunk in page.chunks:
            assert chunk.document_id == str(result.document_id)
            assert chunk.page_number == page.page_number
            assert chunk.chunk_id == (
                f"{result.document_id}:page-{page.page_number}:"
                f"chunk-{chunk.chunk_index}"
            )
            assert chunk.text


def test_multiple_pages_are_cleaned_and_chunked_in_order() -> None:
    events: list[object] = []
    document = make_document(" first ", "second", "third")
    pipeline, _, _, _, chunker = make_pipeline(
        InputType.PDF,
        document,
        events,
        replacements={" first ": "first", "second": "SECOND", "third": "THIRD"},
    )

    result = pipeline.process(make_input("application/pdf"))

    assert [page.page_number for page in result.pages] == [1, 2, 3]
    assert [page.text for page in result.pages] == ["first", "SECOND", "THIRD"]
    assert [page.chunks[0].chunk_index for page in result.pages] == [0, 0, 0]
    assert [page.chunks[0].page_number for page in result.pages] == [1, 2, 3]
    assert chunker.calls == [
        (DOCUMENT_ID, 1, "first"),
        (DOCUMENT_ID, 2, "SECOND"),
        (DOCUMENT_ID, 3, "THIRD"),
    ]
    assert all(document_id == DOCUMENT_ID for document_id, _, _ in chunker.calls)
    assert all(isinstance(document_id, UUID) for document_id, _, _ in chunker.calls)


@pytest.mark.parametrize("text", ["", "   ", "\n\n", "\t"])
def test_empty_and_whitespace_pages_are_not_rejected(text: str) -> None:
    events: list[object] = []
    document = make_document(text)
    pipeline, _, _, _, chunker = make_pipeline(
        InputType.PDF,
        document,
        events,
    )

    result = pipeline.process(make_input("application/pdf"))

    assert result.pages[0].text == text
    assert len(chunker.calls) == 1
    assert chunker.calls[0] == (DOCUMENT_ID, 1, text)


def test_classifier_error_is_propagated() -> None:
    error = RuntimeError("classifier failed")
    events: list[object] = []
    pipeline, pdf_processor, ocr_processor, _, _ = make_pipeline(
        InputType.PDF,
        make_document("text"),
        events,
        classifier_error=error,
    )

    with pytest.raises(RuntimeError) as raised:
        pipeline.process(make_input("application/pdf"))

    assert raised.value is error
    assert pdf_processor.calls == 0
    assert ocr_processor.calls == 0


def test_pdf_processor_error_is_propagated() -> None:
    error = RuntimeError("pdf failed")
    events: list[object] = []
    pipeline, _, _, _, _ = make_pipeline(
        InputType.PDF,
        make_document("text"),
        events,
        pdf_error=error,
    )

    with pytest.raises(RuntimeError) as raised:
        pipeline.process(make_input("application/pdf"))

    assert raised.value is error


def test_ocr_processor_error_is_propagated() -> None:
    error = RuntimeError("ocr failed")
    events: list[object] = []
    pipeline, _, _, _, _ = make_pipeline(
        InputType.IMAGE,
        make_document("text"),
        events,
        ocr_error=error,
    )

    with pytest.raises(RuntimeError) as raised:
        pipeline.process(make_input("image/png"))

    assert raised.value is error


def test_pdf_fallback_propagates_ocr_error() -> None:
    error = OCRProcessingError("ocr fallback failed")
    events: list[object] = []
    pipeline, _, ocr_processor, _, _ = make_pipeline(
        InputType.PDF,
        make_document("", "\t"),
        events,
        ocr_error=error,
    )

    with pytest.raises(OCRProcessingError) as raised:
        pipeline.process(make_input("application/pdf"))

    assert raised.value is error
    assert ocr_processor.calls == 1
    assert events == ["classification", "pdf-processing", "ocr-processing"]


def test_cleaner_error_is_propagated() -> None:
    error = RuntimeError("cleaner failed")
    events: list[object] = []
    pipeline, _, _, _, chunker = make_pipeline(
        InputType.PDF,
        make_document("text"),
        events,
        cleaner_error=error,
    )

    with pytest.raises(RuntimeError) as raised:
        pipeline.process(make_input("application/pdf"))

    assert raised.value is error
    assert chunker.calls == []


def test_chunker_error_is_propagated() -> None:
    error = RuntimeError("chunker failed")
    events: list[object] = []
    pipeline, _, _, _, _ = make_pipeline(
        InputType.PDF,
        make_document("text"),
        events,
        chunker_error=error,
    )

    with pytest.raises(RuntimeError) as raised:
        pipeline.process(make_input("application/pdf"))

    assert raised.value is error
