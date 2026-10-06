"""Rótulos em português para os valores técnicos mostrados na interface."""

import re

STATUS = {
    "higher": "B maior",
    "lower": "B menor",
    "equal": "Igual",
    "different": "Diferente",
    "needs_review": "Revisar",
    "not_comparable": "Não comparável",
}
TONE = {
    "higher": "info", "lower": "info", "equal": "ok",
    "different": "warn", "needs_review": "alert", "not_comparable": "mute",
}
CATEGORIES = ["Todas", "Condições gerais", "Coberturas", "Exclusões", "Extensões"]

_VALUES = {
    "fixed": "Fixa", "percentage": "Percentual", "mixed": "Mista",
    "included": "Incluída", "excluded": "Excluída", "partial": "Parcial",
    "ambiguous": "Ambígua", "identified": "Identificada",
    "not_found": "Não localizado", "not_applicable": "Não se aplica",
    "found": "Encontrado",
}


def pt(text: str) -> str:
    """Traduz códigos internos e moeda para exibição."""
    text = str(text)
    if text in _VALUES:
        return _VALUES[text]
    text = text.replace("BRL ", "R$ ")
    return re.sub(r"\b(fixed|percentage|mixed)\b", lambda m: _VALUES[m.group(1)], text)


def short(text: str) -> str:
    """Versão curta para cartões: só as duas primeiras partes do valor."""
    return " — ".join(pt(text).split(" — ")[:2])


def category_of(criterion: str) -> str:
    if criterion.startswith("Cobertura"):
        return "Coberturas"
    if criterion.startswith("Exclus"):
        return "Exclusões"
    if criterion.startswith("Extens"):
        return "Extensões"
    return "Condições gerais"
