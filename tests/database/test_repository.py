"""Round-trip tests for the optional local analysis history."""

from src.database import SQLiteAnalysisRepository

from tests.comparison.test_comparison_engine import _policy
from src.comparison import ComparisonEngine


def test_repository_saves_and_reads_analysis(tmp_path):
    policy_a = _policy("A", 5_000_000, 50_000)
    policy_b = _policy("B", 10_000_000, 100_000)
    report = ComparisonEngine().compare(policy_a, policy_b)
    repository = SQLiteAnalysisRepository(tmp_path / "history.sqlite3")

    analysis_id = repository.save(policy_a, policy_b, report, "Resumo de teste")
    stored = repository.get(analysis_id)

    assert stored is not None
    assert stored.policy_a.document_id == "A"
    assert stored.report.rows[0].difference.value == "higher"
    assert stored.explanation == "Resumo de teste"
    assert repository.list_recent()[0].analysis_id == analysis_id

