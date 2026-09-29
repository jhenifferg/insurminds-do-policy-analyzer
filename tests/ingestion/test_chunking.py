from uuid import UUID

import pytest

from src.ingestion import Chunker, ExtractionMethod, Page


DOCUMENT_ID = UUID("12345678-1234-5678-1234-567812345678")


def make_page(text: str, page_number: int = 1) -> Page:
    return Page(
        page_number=page_number,
        text=text,
        extraction_method=ExtractionMethod.NATIVE,
    )


def test_empty_page_produces_no_chunks() -> None:
    chunks = Chunker(max_chunk_size=10).chunk_page(
        DOCUMENT_ID, make_page("", page_number=7)
    )

    assert chunks == []


def test_text_shorter_than_limit_produces_one_chunk() -> None:
    chunks = Chunker(max_chunk_size=10).chunk_page(DOCUMENT_ID, make_page("ABC"))

    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].text == "ABC"


def test_text_exactly_at_limit_produces_one_chunk() -> None:
    text = "ABCDEFGHIJ"
    chunks = Chunker(max_chunk_size=10).chunk_page(DOCUMENT_ID, make_page(text))

    assert len(chunks) == 1
    assert chunks[0].text == text


def test_text_larger_than_limit_is_split_by_characters() -> None:
    chunks = Chunker(max_chunk_size=4).chunk_page(
        DOCUMENT_ID, make_page("ABCDEFGHIJ")
    )

    assert [chunk.text for chunk in chunks] == ["ABCD", "EFGH", "IJ"]


def test_concatenation_preserves_page_text_exactly() -> None:
    page = make_page("  Texto  com\twhitespace\n e Unicode: áç R$  ")
    chunks = Chunker(max_chunk_size=7).chunk_page(DOCUMENT_ID, page)

    assert "".join(chunk.text for chunk in chunks) == page.text


@pytest.mark.parametrize("text", ["   ", "\n\n", "\t"])
def test_whitespace_only_text_is_preserved(text: str) -> None:
    chunks = Chunker(max_chunk_size=3).chunk_page(DOCUMENT_ID, make_page(text))

    assert "".join(chunk.text for chunk in chunks) == text
    assert all(chunk.text != "" for chunk in chunks)


def test_whitespace_at_chunk_boundaries_is_preserved() -> None:
    page = make_page("ABC   DEF")
    chunks = Chunker(max_chunk_size=4).chunk_page(DOCUMENT_ID, page)

    assert [chunk.text for chunk in chunks] == ["ABC ", "  DE", "F"]
    assert "".join(chunk.text for chunk in chunks) == page.text


def test_chunk_indexes_are_sequential() -> None:
    chunks = Chunker(max_chunk_size=3).chunk_page(DOCUMENT_ID, make_page("1234567"))

    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))


def test_metadata_is_preserved_and_uuid_is_stored_as_string() -> None:
    chunks = Chunker(max_chunk_size=3).chunk_page(
        DOCUMENT_ID, make_page("123456", page_number=7)
    )

    assert all(isinstance(chunk.document_id, str) for chunk in chunks)
    assert all(chunk.document_id == str(DOCUMENT_ID) for chunk in chunks)
    assert all(chunk.page_number == 7 for chunk in chunks)


def test_max_chunk_size_one_creates_one_chunk_per_character() -> None:
    text = "A \nB"
    chunks = Chunker(max_chunk_size=1).chunk_page(DOCUMENT_ID, make_page(text))

    assert [chunk.text for chunk in chunks] == list(text)
    assert "".join(chunk.text for chunk in chunks) == text


def test_all_chunks_respect_maximum_size() -> None:
    max_chunk_size = 4
    chunks = Chunker(max_chunk_size=max_chunk_size).chunk_page(
        DOCUMENT_ID, make_page("ABCDEFGHIJK")
    )

    assert all(len(chunk.text) <= max_chunk_size for chunk in chunks)


@pytest.mark.parametrize("max_chunk_size", [0, -1])
def test_max_chunk_size_must_be_positive(max_chunk_size: int) -> None:
    with pytest.raises(ValueError):
        Chunker(max_chunk_size=max_chunk_size)


def test_chunking_is_deterministic() -> None:
    page = make_page("Deterministic text\nwith whitespace")
    chunker = Chunker(max_chunk_size=5)

    first = chunker.chunk_page(DOCUMENT_ID, page)
    second = chunker.chunk_page(DOCUMENT_ID, page)

    assert first == second


def test_each_page_is_processed_independently() -> None:
    chunker = Chunker(max_chunk_size=4)
    first_page_chunks = chunker.chunk_page(
        DOCUMENT_ID, make_page("abcdefgh", page_number=1)
    )
    second_page_chunks = chunker.chunk_page(
        DOCUMENT_ID, make_page("12345678", page_number=2)
    )

    assert [chunk.page_number for chunk in first_page_chunks] == [1, 1]
    assert [chunk.page_number for chunk in second_page_chunks] == [2, 2]
    assert "".join(chunk.text for chunk in first_page_chunks) == "abcdefgh"
    assert "".join(chunk.text for chunk in second_page_chunks) == "12345678"


def test_page_is_not_modified_by_chunking() -> None:
    page = make_page("A  B\nC")
    original_text = page.text

    Chunker(max_chunk_size=2).chunk_page(DOCUMENT_ID, page)

    assert page.text == original_text
