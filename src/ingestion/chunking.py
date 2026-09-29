"""Deterministic page-level text chunking."""

from uuid import UUID

from .models import Chunk, Page


class Chunker:
    """Split page text into fixed-size, non-overlapping character chunks."""

    DEFAULT_MAX_CHUNK_SIZE = 1000

    def __init__(self, max_chunk_size: int = DEFAULT_MAX_CHUNK_SIZE) -> None:
        if (
            isinstance(max_chunk_size, bool)
            or not isinstance(max_chunk_size, int)
            or max_chunk_size <= 0
        ):
            raise ValueError("max_chunk_size must be a positive integer")
        self.max_chunk_size = max_chunk_size

    def chunk_page(self, document_id: UUID, page: Page) -> list[Chunk]:
        """Partition one page's text while preserving its exact provenance."""
        if not isinstance(document_id, UUID):
            raise TypeError("document_id must be a UUID")
        if not isinstance(page, Page):
            raise TypeError("page must be a Page instance")
        if page.text == "":
            return []

        chunks: list[Chunk] = []
        for chunk_index, start in enumerate(
            range(0, len(page.text), self.max_chunk_size)
        ):
            chunk_text = page.text[start : start + self.max_chunk_size]
            chunks.append(
                Chunk(
                    chunk_id=(
                        f"{document_id}:page-{page.page_number}:chunk-{chunk_index}"
                    ),
                    document_id=str(document_id),
                    page_number=page.page_number,
                    chunk_index=chunk_index,
                    text=chunk_text,
                )
            )
        return chunks
