"""Deterministic policy comparison tests."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from src.comparison import ComparisonEngine, DifferenceKind
from src.extraction import (
    ClauseNormalizer,
    CoverageFinding,
    Deductible,
    Evidence,
    ExclusionFinding,
    ExtractionStatus,
    FieldValue,
    MoneyAmount,
    PolicyExtraction,
)


def _evidence(document_id: str, quote: str) -> Evidence:
    return Evidence(
        document_id=document_id,
        page_number=1,
        chunk_id=f"{document_id}:page-1:chunk-0",
        quote=quote,
    )


def _missing():
    return FieldValue(status=ExtractionStatus.NOT_FOUND)


def _policy(document_id: str, lmg: int, deductible: int, *, include_side_a=True):
    ev = _evidence(document_id, f"LMG {lmg}")
    fields = {name: _missing() for name in (
        "insurer policy_number endorsement product line_of_business issue_date "
        "insured_name insured_cnpj effective_start effective_end retroactivity_date "
        "extended_reporting_period supplementary_period run_off lmi_sublimits "
        "deductibles coverages exclusions extensions"
    ).split()}
    fields["lmg"] = FieldValue(
        status=ExtractionStatus.FOUND,
        value=MoneyAmount(amount=lmg, currency="BRL"),
        evidence=[ev],
    )
    fields["deductibles"] = FieldValue(
        status=ExtractionStatus.FOUND,
        value=[Deductible(kind="fixed", amount=MoneyAmount(amount=deductible, currency="BRL"))],
        evidence=[ev],
    )
    coverages = []
    if include_side_a:
        coverages.append(CoverageFinding(
            name="Side A", status="included", evidence=[ev]
        ))
    fields["coverages"] = FieldValue(
        status=ExtractionStatus.FOUND, value=coverages, evidence=[ev]
    )
    fields["exclusions"] = FieldValue(
        status=ExtractionStatus.FOUND,
        value=[ExclusionFinding(name="Fraude", evidence=[ev])],
        evidence=[ev],
    )
    return PolicyExtraction(
        schema_version="1.0",
        document_id=document_id,
        filename=f"{document_id}.pdf",
        **fields,
    )


def test_comparison_reports_numeric_differences_and_evidence():
    report = ComparisonEngine().compare(
        _policy("A", 5_000_000, 50_000),
        _policy("B", 10_000_000, 100_000),
    )

    lmg = next(row for row in report.rows if row.criterion.startswith("Limite Máximo"))
    deductible = next(row for row in report.rows if row.criterion == "Franquia / retenção")
    assert lmg.difference is DifferenceKind.HIGHER
    assert deductible.difference is DifferenceKind.HIGHER
    assert lmg.evidence_policy_a[0].document_id == "A"


def test_coverage_not_found_in_one_document_is_not_called_absent():
    report = ComparisonEngine().compare(
        _policy("A", 5_000_000, 50_000),
        _policy("B", 5_000_000, 50_000, include_side_a=False),
    )
    row = next(row for row in report.rows if row.criterion == "Cobertura: Side A")
    assert row.difference is DifferenceKind.NEEDS_REVIEW


def test_name_variants_for_dno_liability_coverage_compare_as_same_coverage():
    a = _policy("doc-a", 5_000_000, 50_000)
    b = _policy("doc-b", 10_000_000, 100_000)
    ev_a = _evidence("doc-a", "Cobertura A - Responsabilidade de administradores e diretores")
    ev_b = _evidence("doc-b", "Cobertura A - Responsabilidade de administradores e diretores por reclamacoes")
    a.coverages = FieldValue(
        status=ExtractionStatus.FOUND,
        value=[CoverageFinding(
            name="Cobertura A - Responsabilidade de administradores e diretores",
            status="included", evidence=[ev_a],
        )],
        evidence=[ev_a],
    )
    b.coverages = FieldValue(
        status=ExtractionStatus.FOUND,
        value=[CoverageFinding(
            name="Cobertura A - Responsabilidade de administradores e diretores por reclamacoes",
            status="included", evidence=[ev_b],
        )],
        evidence=[ev_b],
    )

    normalizer = ClauseNormalizer()
    normalizer.normalize(a)
    normalizer.normalize(b)
    report = ComparisonEngine().compare(a, b)
    coverage_rows = [row for row in report.rows if row.criterion.startswith("Cobertura:")]

    assert len(coverage_rows) == 1
    assert coverage_rows[0].difference is DifferenceKind.EQUAL


def test_name_variants_for_corporate_reimbursement_compare_as_same_coverage():
    a = _policy("doc-a", 5_000_000, 50_000, include_side_a=False)
    b = _policy("doc-b", 10_000_000, 100_000, include_side_a=False)
    ev_a = _evidence("doc-a", "Cobertura B - Reembolso a sociedade")
    ev_b = _evidence(
        "doc-b",
        "Cobertura B - Reembolso a sociedade por valores pagos em nome de administrador segurado",
    )
    a.coverages = FieldValue(
        status=ExtractionStatus.FOUND,
        value=[CoverageFinding(
            name="Cobertura B - Reembolso a sociedade",
            status="included", evidence=[ev_a],
        )],
        evidence=[ev_a],
    )
    b.coverages = FieldValue(
        status=ExtractionStatus.FOUND,
        value=[CoverageFinding(
            name="Cobertura B - Reembolso a sociedade por valores pagos em nome de administrador segurado",
            status="included", evidence=[ev_b],
        )],
        evidence=[ev_b],
    )

    normalizer = ClauseNormalizer()
    normalizer.normalize(a)
    normalizer.normalize(b)
    report = ComparisonEngine().compare(a, b)
    coverage_rows = [row for row in report.rows if row.criterion.startswith("Cobertura:")]

    assert len(coverage_rows) == 1
    assert coverage_rows[0].difference is DifferenceKind.EQUAL


def test_name_variants_for_bodily_injury_exclusion_compare_as_same_clause():
    a = _policy("doc-a", 5_000_000, 50_000)
    b = _policy("doc-b", 10_000_000, 100_000)
    ev_a = _evidence("doc-a", "danos corporais e materiais, salvo extensão expressa.")
    ev_b = _evidence("doc-b", "danos corporais e materiais, salvo extensão expressa")
    a.exclusions = FieldValue(
        status=ExtractionStatus.FOUND,
        value=[ExclusionFinding(
            name="Danos corporais e materiais",
            trigger="danos corporais e materiais, salvo extensão expressa.",
            evidence=[ev_a],
        )],
        evidence=[ev_a],
    )
    b.exclusions = FieldValue(
        status=ExtractionStatus.FOUND,
        value=[ExclusionFinding(
            name="Danos corporais e materiais, salvo extensão expressa",
            trigger="danos corporais e materiais, salvo extensão expressa",
            evidence=[ev_b],
        )],
        evidence=[ev_b],
    )

    normalizer = ClauseNormalizer()
    normalizer.normalize(a)
    normalizer.normalize(b)
    report = ComparisonEngine().compare(a, b)
    exclusion_rows = [row for row in report.rows if row.criterion.startswith("Exclusão:")]

    assert len(exclusion_rows) == 1
    assert exclusion_rows[0].difference is DifferenceKind.EQUAL


def test_extensions_are_included_in_comparison():
    a = _policy("doc-a", 5_000_000, 50_000)
    b = _policy("doc-b", 10_000_000, 100_000)
    ev_a = _evidence("doc-a", "Custos de defesa podem integrar o LMG")
    ev_b = _evidence("doc-b", "Custos de defesa podem integrar o LMG")
    for policy, evidence in ((a, ev_a), (b, ev_b)):
        policy.extensions = FieldValue(
            status=ExtractionStatus.FOUND,
            value=[CoverageFinding(
                name="Custos de defesa",
                status="included",
                evidence=[evidence],
            )],
            evidence=[evidence],
        )

    ClauseNormalizer().normalize(a)
    ClauseNormalizer().normalize(b)
    report = ComparisonEngine().compare(a, b)
    extension_row = next(row for row in report.rows if row.criterion == "Extensão: Custos de defesa")

    assert extension_row.difference is DifferenceKind.EQUAL
