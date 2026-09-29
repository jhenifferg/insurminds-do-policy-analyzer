"""Deterministic classification of supported document inputs."""

from enum import Enum

from .exceptions import UnsupportedDocumentError
from .models import DocumentInput


class InputType(str, Enum):
    """Supported high-level input categories."""

    PDF = "pdf"
    IMAGE = "image"


class InputClassifier:
    """Classify inputs using their declared MIME type."""

    _MEDIA_TYPES = {
        "application/pdf": InputType.PDF,
        "image/jpeg": InputType.IMAGE,
        "image/png": InputType.IMAGE,
    }

    def classify(self, document: DocumentInput) -> InputType:
        """Return the supported input type or reject the MIME type."""
        try:
            return self._MEDIA_TYPES[document.media_type]
        except KeyError as exc:
            raise UnsupportedDocumentError(
                f"Unsupported document media type: {document.media_type}"
            ) from exc
