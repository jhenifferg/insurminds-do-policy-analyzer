"""Deterministic comparison of normalized, evidence-backed D&O extractions."""

from decimal import Decimal
import re
import unicodedata

from src.extraction.models import (
    CoverageFinding,
    ExclusionFinding,
    ExtractionStatus,
    FieldValue,
    MoneyAmount,
    PolicyExtraction,
)

from .models import ComparisonReport, ComparisonRow, DifferenceKind


class ComparisonEngine:
    """Compare explicit values only; never interpret missing fields as no cover."""

    def compare(
        self, policy_a: PolicyExtraction, policy_b: PolicyExtraction
    ) -> ComparisonReport:
        rows = [
            self._money_row("Limite Máximo de Garantia (LMG)", policy_a.lmg, policy_b.lmg),
            self._deductible_row(policy_a, policy_b),
        ]
        rows.extend(_clause_rows("LMI / sublimite", policy_a.lmi_sublimits, policy_b.lmi_sublimits))
        rows.extend(self._coverage_rows(policy_a, policy_b))
        rows.extend(self._extension_rows(policy_a, policy_b))
        rows.extend(self._exclusion_rows(policy_a, policy_b))
        return ComparisonReport(
            policy_a_document_id=policy_a.document_id,
            policy_a_name=policy_a.filename,
            policy_b_document_id=policy_b.document_id,
            policy_b_name=policy_b.filename,
            rows=rows,
        )

    @staticmethod
    def _money_row(
        label: str,
        a: FieldValue[MoneyAmount],
        b: FieldValue[MoneyAmount],
    ) -> ComparisonRow:
        if a.status is not ExtractionStatus.FOUND or b.status is not ExtractionStatus.FOUND:
            return _unknown_row(
                label, a.status.value, b.status.value,
                evidence_a=a.evidence, evidence_b=b.evidence,
            )
        av, bv = a.value, b.value
        assert av is not None and bv is not None
        return ComparisonEngine._money_values_row(
            label, av, bv, evidence_a=a.evidence, evidence_b=b.evidence
        )

    @staticmethod
    def _money_values_row(
        label: str,
        av: MoneyAmount,
        bv: MoneyAmount,
        *,
        evidence_a=(),
        evidence_b=(),
    ) -> ComparisonRow:
        if av.currency != bv.currency:
            return ComparisonRow(
                criterion=label,
                policy_a=_format_money(av),
                policy_b=_format_money(bv),
                difference=DifferenceKind.NOT_COMPARABLE,
                explanation="Moedas diferentes; é necessária conversão com critério definido.",
                evidence_policy_a=list(evidence_a), evidence_policy_b=list(evidence_b),
            )
        kind = _direction(av.amount, bv.amount)
        difference = {
            DifferenceKind.HIGHER: f"B apresenta {label} nominal maior.",
            DifferenceKind.LOWER: f"B apresenta {label} nominal menor.",
            DifferenceKind.EQUAL: "Valores nominais iguais.",
        }[kind]
        return ComparisonRow(
            criterion=label,
            policy_a=_format_money(av),
            policy_b=_format_money(bv),
            difference=kind,
            explanation=difference,
            evidence_policy_a=list(evidence_a), evidence_policy_b=list(evidence_b),
        )

    @staticmethod
    def _deductible_row(
        policy_a: PolicyExtraction, policy_b: PolicyExtraction
    ) -> ComparisonRow:
        a, b = policy_a.deductibles, policy_b.deductibles
        if (
            a.status is not ExtractionStatus.FOUND
            or b.status is not ExtractionStatus.FOUND
            or a.value is None
            or b.value is None
            or len(a.value) != 1
            or len(b.value) != 1
        ):
            return _unknown_row(
                "Franquia / retenção",
                _status_or_count(a),
                _status_or_count(b),
                evidence_a=a.evidence, evidence_b=b.evidence,
            )
        da, db = a.value[0], b.value[0]
        if (
            da.kind != db.kind
            or da.kind == "mixed"
            or (da.amount and db.amount and da.amount.currency != db.amount.currency)
        ):
            return ComparisonRow(
                criterion="Franquia / retenção",
                policy_a=_format_deductible(da),
                policy_b=_format_deductible(db),
                difference=DifferenceKind.NOT_COMPARABLE,
                explanation="Tipos ou moedas de franquia diferentes; requerem normalização.",
                evidence_policy_a=a.evidence, evidence_policy_b=b.evidence,
            )
        if da.kind == "fixed" and da.amount and db.amount:
            kind = _direction(da.amount.amount, db.amount.amount)
        elif da.kind == "percentage" and da.percentage is not None and db.percentage is not None:
            if (
                not da.percentage_basis
                or not db.percentage_basis
                or _normalize(da.percentage_basis) != _normalize(db.percentage_basis)
            ):
                kind = DifferenceKind.NOT_COMPARABLE
            else:
                kind = _direction(da.percentage, db.percentage)
        else:
            kind = DifferenceKind.NEEDS_REVIEW
        explanation = {
            DifferenceKind.HIGHER: "B apresenta franquia/retenção nominal maior.",
            DifferenceKind.LOWER: "B apresenta franquia/retenção nominal menor.",
            DifferenceKind.EQUAL: "Valores nominais iguais.",
            DifferenceKind.NEEDS_REVIEW: "Estruturas mistas exigem análise das condições e da base de cálculo.",
            DifferenceKind.NOT_COMPARABLE: "Bases percentuais diferentes ou não informadas; requer revisão.",
        }[kind]
        return ComparisonRow(
            criterion="Franquia / retenção",
            policy_a=_format_deductible(da),
            policy_b=_format_deductible(db),
            difference=kind,
            explanation=explanation,
            evidence_policy_a=a.evidence, evidence_policy_b=b.evidence,
        )

    @staticmethod
    def _coverage_rows(a: PolicyExtraction, b: PolicyExtraction) -> list[ComparisonRow]:
        return _clause_rows("Cobertura", a.coverages, b.coverages)

    @staticmethod
    def _extension_rows(a: PolicyExtraction, b: PolicyExtraction) -> list[ComparisonRow]:
        return _clause_rows("Extensão", a.extensions, b.extensions)

    @staticmethod
    def _exclusion_rows(a: PolicyExtraction, b: PolicyExtraction) -> list[ComparisonRow]:
        left = a.exclusions
        right = b.exclusions
        if left.status is not ExtractionStatus.FOUND or right.status is not ExtractionStatus.FOUND:
            return [_unknown_row(
                "Exclusões", left.status.value, right.status.value,
                evidence_a=left.evidence, evidence_b=right.evidence,
            )]
        assert left.value is not None and right.value is not None
        left_map = {_exclusion_key(item): item for item in left.value}
        right_map = {_exclusion_key(item): item for item in right.value}
        rows: list[ComparisonRow] = []
        for key in sorted(left_map.keys() | right_map.keys()):
            item_a, item_b = left_map.get(key), right_map.get(key)
            label = (item_a or item_b).name
            if item_a is None or item_b is None:
                rows.append(_unknown_row(
                    f"Exclusão: {label}", "mencionada", "não localizada",
                    evidence_a=item_a.evidence if item_a else [],
                    evidence_b=item_b.evidence if item_b else [],
                ))
            elif item_a.status == "ambiguous" or item_b.status == "ambiguous":
                rows.append(ComparisonRow(
                    criterion=f"Exclusão: {label}", policy_a=item_a.trigger or "Ambígua",
                    policy_b=item_b.trigger or "Ambígua", difference=DifferenceKind.NEEDS_REVIEW,
                    explanation="A extração encontrou trechos divergentes; requer revisão especializada.",
                    evidence_policy_a=item_a.evidence, evidence_policy_b=item_b.evidence,
                ))
            elif _normalize(item_a.trigger or "") == _normalize(item_b.trigger or ""):
                rows.append(ComparisonRow(
                    criterion=f"Exclusão: {label}", policy_a=item_a.trigger or "Identificada",
                    policy_b=item_b.trigger or "Identificada", difference=DifferenceKind.EQUAL,
                    explanation="A exclusão foi identificada em ambas; equivalência jurídica não avaliada.",
                    evidence_policy_a=item_a.evidence, evidence_policy_b=item_b.evidence,
                ))
            else:
                rows.append(ComparisonRow(
                    criterion=f"Exclusão: {label}", policy_a=item_a.trigger or "Identificada",
                    policy_b=item_b.trigger or "Identificada", difference=DifferenceKind.NEEDS_REVIEW,
                    explanation="Os gatilhos ou trechos diferem e exigem revisão especializada.",
                    evidence_policy_a=item_a.evidence, evidence_policy_b=item_b.evidence,
                ))
        return rows


def _clause_rows(
    label: str,
    a: FieldValue[list[CoverageFinding]],
    b: FieldValue[list[CoverageFinding]],
) -> list[ComparisonRow]:
    if a.status is not ExtractionStatus.FOUND or b.status is not ExtractionStatus.FOUND:
        return [_unknown_row(
            f"{label}s", a.status.value, b.status.value,
            evidence_a=a.evidence, evidence_b=b.evidence,
        )]
    assert a.value is not None and b.value is not None
    left = {_coverage_key(item): item for item in a.value}
    right = {_coverage_key(item): item for item in b.value}
    rows: list[ComparisonRow] = []
    for key in sorted(left.keys() | right.keys()):
        ca, cb = left.get(key), right.get(key)
        name = (ca or cb).name
        if ca is None or cb is None:
            rows.append(_unknown_row(
                f"{label}: {name}", "mencionada", "não localizada",
                evidence_a=ca.evidence if ca else [], evidence_b=cb.evidence if cb else [],
            ))
            continue
        if ca.limit and cb.limit:
            money = ComparisonEngine._money_values_row(
                f"{label}: {name} — limite", ca.limit, cb.limit,
                evidence_a=ca.evidence, evidence_b=cb.evidence,
            )
            rows.append(money)
        sa, sb = _normalize(ca.status), _normalize(cb.status)
        if sa == sb and sa == "ambiguous":
            rows.append(ComparisonRow(
                criterion=f"{label}: {name}", policy_a=ca.status, policy_b=cb.status,
                difference=DifferenceKind.NEEDS_REVIEW,
                explanation="A extração encontrou mais de uma interpretação; requer revisão.",
                evidence_policy_a=ca.evidence, evidence_policy_b=cb.evidence,
            ))
        elif sa == sb:
            rows.append(ComparisonRow(
                criterion=f"{label}: {name}", policy_a=ca.status, policy_b=cb.status,
                difference=DifferenceKind.EQUAL, explanation="Estado extraído igual nas duas apólices.",
                evidence_policy_a=ca.evidence, evidence_policy_b=cb.evidence,
            ))
        else:
            rows.append(ComparisonRow(
                criterion=f"{label}: {name}", policy_a=ca.status, policy_b=cb.status,
                difference=DifferenceKind.DIFFERENT,
                explanation="Os estados extraídos diferem; rever o texto e as condições da cláusula.",
                evidence_policy_a=ca.evidence, evidence_policy_b=cb.evidence,
            ))
    return rows


def _coverage_key(item: CoverageFinding) -> str:
    return item.taxonomy_code.upper() if item.taxonomy_code else _normalize(item.name)


def _exclusion_key(item: ExclusionFinding) -> str:
    return item.category.upper() if item.category else _normalize(item.name)


def _normalize(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\W+", " ", folded).strip()


def _direction(a: Decimal, b: Decimal) -> DifferenceKind:
    if b > a:
        return DifferenceKind.HIGHER
    if b < a:
        return DifferenceKind.LOWER
    return DifferenceKind.EQUAL


def _format_money(value: MoneyAmount) -> str:
    integer, _, cents = f"{value.amount:,.2f}".partition(".")
    return f"{value.currency} {integer.replace(',', '.')},{cents}"


def _format_deductible(value) -> str:
    pieces = [value.kind]
    if value.amount:
        pieces.append(_format_money(value.amount))
    if value.percentage is not None:
        pieces.append(f"{value.percentage}%")
    if value.percentage_basis:
        pieces.append(f"base: {value.percentage_basis}")
    if value.description:
        pieces.append(value.description)
    return " — ".join(pieces)


def _status_or_count(field) -> str:
    return field.status.value if field.status is not ExtractionStatus.FOUND else f"{len(field.value or [])} itens"


def _unknown_row(label: str, a: str, b: str, *, evidence_a=(), evidence_b=()) -> ComparisonRow:
    return ComparisonRow(
        criterion=label,
        policy_a=a,
        policy_b=b,
        difference=DifferenceKind.NEEDS_REVIEW,
        explanation="Não há dados comparáveis suficientes; não se infere ausência de cobertura.",
        evidence_policy_a=list(evidence_a), evidence_policy_b=list(evidence_b),
    )


__all__ = ["ComparisonEngine"]
