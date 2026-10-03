"""Grounded narrative explanation of a deterministic comparison report."""

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from src.comparison.models import ComparisonReport


class TextLLM(Protocol):
    def complete_text(self, *, system_prompt: str, user_prompt: str) -> str: ...


class ExplanationAgent:
    """Explain listed differences without ranking policies or filling gaps."""

    def __init__(self, llm: TextLLM) -> None:
        self.llm = llm

    def explain(self, report: "ComparisonReport") -> str:
        return self.llm.complete_text(
            system_prompt=(
                "Explique somente os fatos estruturados fornecidos. Não complete lacunas, "
                "não use conhecimento externo, não conclua qual apólice é melhor e não "
                "trate informação não localizada como cobertura inexistente. Destaque "
                "itens que requerem revisão humana."
            ),
            user_prompt=(
                "Explique as diferenças e possíveis implicações com base exclusivamente "
                "nesta comparação. Preserve a distinção entre diferença confirmada e "
                "ponto pendente de revisão.\n\n" + report.model_dump_json(indent=2)
            ),
        )


__all__ = ["ExplanationAgent", "TextLLM"]
