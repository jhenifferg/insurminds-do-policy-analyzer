"""Deterministic page-level text chunking that avoids splitting source lines."""

from uuid import UUID

from .models import Chunk, Page


class Chunker:
    """Split page text into non-overlapping chunks, preferring line/word boundaries."""

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
        start = 0
        while start < len(page.text):
            end = min(start + self.max_chunk_size, len(page.text))
            if end < len(page.text):
                window = page.text[start:end]
                newline = window.rfind("\n")
                whitespace = max(window.rfind(" "), window.rfind("\t"), window.rfind("\r"))
                if newline >= self.max_chunk_size // 2:
                    end = start + newline + 1
                elif whitespace >= self.max_chunk_size // 2:
                    end = start + whitespace + 1

            chunk_text = page.text[start:end]
            chunks.append(
                Chunk(
                    chunk_id=(
                        f"{document_id}:page-{page.page_number}:chunk-{len(chunks)}"
                    ),
                    document_id=str(document_id),
                    page_number=page.page_number,
                    chunk_index=len(chunks),
                    text=chunk_text,
                )
            )
            start = end
        return chunks
