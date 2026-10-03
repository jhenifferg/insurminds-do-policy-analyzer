"""Local SQLite history for structured policy comparisons."""

from dataclasses import dataclass
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3

from src.comparison.models import ComparisonReport
from src.extraction.models import PolicyExtraction


@dataclass(frozen=True)
class AnalysisSummary:
    analysis_id: int
    created_at: str
    policy_a_name: str
    policy_b_name: str


@dataclass(frozen=True)
class StoredAnalysis:
    analysis_id: int
    created_at: str
    policy_a: PolicyExtraction
    policy_b: PolicyExtraction
    report: ComparisonReport
    explanation: str | None


class SQLiteAnalysisRepository:
    """Persist extracted JSON and comparison output in a local SQLite file."""

    def __init__(self, database_path: str | Path = "data/insurminds.sqlite3") -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    policy_a_json TEXT NOT NULL,
                    policy_b_json TEXT NOT NULL,
                    report_json TEXT NOT NULL,
                    explanation TEXT
                )"""
            )

    def save(
        self,
        policy_a: PolicyExtraction,
        policy_b: PolicyExtraction,
        report: ComparisonReport,
        explanation: str | None = None,
    ) -> int:
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            cursor = connection.execute(
                """INSERT INTO analyses
                   (created_at, policy_a_json, policy_b_json, report_json, explanation)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    created_at,
                    policy_a.model_dump_json(),
                    policy_b.model_dump_json(),
                    report.model_dump_json(),
                    explanation,
                ),
            )
            return int(cursor.lastrowid)

    def list_recent(self, limit: int = 20) -> list[AnalysisSummary]:
        if limit < 1:
            raise ValueError("limit must be positive")
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT id, created_at, policy_a_json, policy_b_json
                   FROM analyses ORDER BY id DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        return [
            AnalysisSummary(
                analysis_id=row["id"],
                created_at=row["created_at"],
                policy_a_name=json.loads(row["policy_a_json"])["filename"],
                policy_b_name=json.loads(row["policy_b_json"])["filename"],
            )
            for row in rows
        ]

    def get(self, analysis_id: int) -> StoredAnalysis | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM analyses WHERE id = ?", (analysis_id,)
            ).fetchone()
        if row is None:
            return None
        return StoredAnalysis(
            analysis_id=row["id"],
            created_at=row["created_at"],
            policy_a=PolicyExtraction.model_validate_json(row["policy_a_json"]),
            policy_b=PolicyExtraction.model_validate_json(row["policy_b_json"]),
            report=ComparisonReport.model_validate_json(row["report_json"]),
            explanation=row["explanation"],
        )


__all__ = ["AnalysisSummary", "SQLiteAnalysisRepository", "StoredAnalysis"]
