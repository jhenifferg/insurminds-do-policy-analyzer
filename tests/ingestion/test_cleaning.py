from src.ingestion import TextCleaner


def test_clean_empty_string() -> None:
    assert TextCleaner().clean("") == ""


def test_removes_outer_spaces() -> None:
    assert TextCleaner().clean("   Texto   ") == "Texto"


def test_normalizes_crlf_newlines() -> None:
    assert TextCleaner().clean("linha 1\r\nlinha 2") == "linha 1\nlinha 2"


def test_normalizes_isolated_carriage_returns() -> None:
    assert TextCleaner().clean("linha 1\rlinha 2") == "linha 1\nlinha 2"


def test_normalizes_redundant_horizontal_whitespace() -> None:
    assert TextCleaner().clean("Nome:\t   João    Silva") == "Nome: João Silva"


def test_reduces_excess_blank_lines_but_preserves_paragraph_break() -> None:
    text = "Parágrafo 1\n\n\n\nParágrafo 2"

    assert TextCleaner().clean(text) == "Parágrafo 1\n\nParágrafo 2"


def test_preserves_legal_values_and_dates() -> None:
    text = "R$ 1.500.000,00 | 10% | 01/01/2026 | Cláusula 4.2"
    cleaned = TextCleaner().clean(text)

    assert "R$ 1.500.000,00" in cleaned
    assert "10%" in cleaned
    assert "01/01/2026" in cleaned
    assert "Cláusula 4.2" in cleaned


def test_preserves_unicode_characters() -> None:
    text = "á ã ç é ê"

    assert TextCleaner().clean(text) == text


def test_preserves_punctuation_and_symbols() -> None:
    text = "() [] {} : ; / - % R$"

    assert TextCleaner().clean(text) == text


def test_already_clean_text_is_unchanged() -> None:
    text = "Linha 1\n\nLinha 2"

    assert TextCleaner().clean(text) == text


def test_cleaner_is_idempotent() -> None:
    cleaner = TextCleaner()
    text = "  Linha 1\r\n\r\n\r\nLinha 2  "

    assert cleaner.clean(cleaner.clean(text)) == cleaner.clean(text)


def test_does_not_reconstruct_hyphenated_words() -> None:
    text = "respon-\nsabilidade"

    assert TextCleaner().clean(text) == text


def test_preserves_content_of_a_fictional_legal_clause() -> None:
    text = (
        "  Cláusula 4.2:\r\n"
        "A seguradora pagará até R$ 1.500.000,00, limitada a 10% "
        "da importância segurada.\r\n\r\n\r\n"
        "Vigência: 01/01/2026 a 31/12/2026.  "
    )

    cleaned = TextCleaner().clean(text)

    assert "Cláusula 4.2:" in cleaned
    assert "R$ 1.500.000,00" in cleaned
    assert "10%" in cleaned
    assert "Vigência: 01/01/2026 a 31/12/2026." in cleaned
