from inspect import signature
from typing import get_type_hints

import pytest

from src.ingestion import (
    Document,
    DocumentInput,
    InputClassifier,
    InputType,
    OCRProcessor,
    UnsupportedDocumentError,
)


def make_input(media_type: str) -> DocumentInput:
    return DocumentInput(
        filename="document.bin",
        media_type=media_type,
        content=b"document-content",
    )


@pytest.mark.parametrize(
    ("media_type", "expected_type"),
    [
        ("application/pdf", InputType.PDF),
        ("image/jpeg", InputType.IMAGE),
        ("image/png", InputType.IMAGE),
    ],
)
def test_classifier_identifies_supported_inputs(
    media_type: str, expected_type: InputType
) -> None:
    assert InputClassifier().classify(make_input(media_type)) is expected_type


def test_classifier_rejects_unsupported_media_type() -> None:
    with pytest.raises(UnsupportedDocumentError):
        InputClassifier().classify(make_input("application/octet-stream"))


def test_ocr_processor_defines_document_input_to_document_contract() -> None:
    assert getattr(OCRProcessor, "_is_protocol", False) is True

    annotations = get_type_hints(OCRProcessor.process)
    parameters = signature(OCRProcessor.process).parameters

    assert list(parameters) == ["self", "document"]
    assert annotations["document"] is DocumentInput
    assert annotations["return"] is Document
