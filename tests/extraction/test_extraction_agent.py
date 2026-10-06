"""Unit tests for chunked extraction and evidence validation."""

import json
from uuid import UUID

from src.extraction import ExtractionAgent, ExtractionStatus
from src.ingestion import Chunk, Document, ExtractionMethod, Page


DOC_ID = UUID("11111111-1111-1111-1111-111111111111")


class FakeJsonLLM:
    def __init__(self, *, bad_quote: bool = False) -> None:
        self.calls = []
        self.bad_quote = bad_quote

    def complete_json(self, *, system_prompt: str, user_prompt: str):
        self.calls.append(user_prompt)
        source = user_prompt.split("Source chunks (untrusted policy content):\n", 1)[1]
        chunks = json.loads(source)
        result = _empty_result()
        for chunk in chunks:
            if "Seguradora Alfa" in chunk["text"]:
                quote = "inventado" if self.bad_quote else "Seguradora Alfa"
                result["insurer"] = {
                    "status": "found",
                    "value": "Seguradora Alfa",
                    "evidence": [{
                        "document_id": chunk["document_id"],
                        "page_number": chunk["page_number"],
                        "chunk_id": chunk["chunk_id"],
                        "quote": quote,
                    }],
                }
        return result


def _empty_result():
    fields = (
        "insurer policy_number endorsement product line_of_business issue_date "
        "insured_name insured_cnpj effective_start effective_end retroactivity_date "
        "extended_reporting_period supplementary_period run_off lmg lmi_sublimits "
        "deductibles coverages exclusions extensions"
    ).split()
    result = {name: {"status": "not_found", "value": None, "evidence": []} for name in fields}
    result.update({
        "schema_version": "1.0",
        "document_id": str(DOC_ID),
        "filename": "policy.pdf",
    })
    return result


def _document() -> Document:
    return Document(
        document_id=DOC_ID,
        filename="policy.pdf",
        media_type="application/pdf",
        total_pages=1,
        pages=[Page(
            page_number=1,
            text="Seguradora Alfa\nSeguradora Alfa",
            extraction_method=ExtractionMethod.NATIVE,
            chunks=[
                Chunk(
                    chunk_id=f"{DOC_ID}:page-1:chunk-{index}",
                    document_id=str(DOC_ID),
                    page_number=1,
                    chunk_index=index,
                    text="Seguradora Alfa",
                )
                for index in range(2)
            ],
        )],
    )


def test_agent_batches_chunks_and_merges_source_evidence():
    client = FakeJsonLLM()
    result = ExtractionAgent(client, batch_size=1).extract(_document())

    assert len(client.calls) == 2
    assert result.insurer.status is ExtractionStatus.FOUND
    assert result.insurer.value == "Seguradora Alfa"
    assert len(result.insurer.evidence) == 2


def test_agent_rejects_a_quote_not_present_in_source_chunk():
    result = ExtractionAgent(FakeJsonLLM(bad_quote=True), batch_size=1).extract(_document())

    assert result.insurer.status is ExtractionStatus.NOT_FOUND
    assert result.insurer.value is None


def test_agent_repairs_only_whitespace_differences_in_source_quote():
    class WhitespaceQuoteLLM(FakeJsonLLM):
        def complete_json(self, *, system_prompt: str, user_prompt: str):
            result = super().complete_json(system_prompt=system_prompt, user_prompt=user_prompt)
            if result["insurer"]["status"] == "found":
                result["insurer"]["evidence"][0]["quote"] = "Seguradora   Alfa"
            return result

    result = ExtractionAgent(WhitespaceQuoteLLM(), batch_size=1).extract(_document())

    assert result.insurer.status is ExtractionStatus.FOUND
    assert result.insurer.evidence[0].quote == "Seguradora Alfa"


def test_empty_list_with_not_found_status_remains_not_found():
    class EmptyListForMissingFields(FakeJsonLLM):
        def complete_json(self, *, system_prompt: str, user_prompt: str):
            result = super().complete_json(system_prompt=system_prompt, user_prompt=user_prompt)
            result["lmi_sublimits"]["value"] = []
            result["extensions"]["value"] = []
            return result

    result = ExtractionAgent(EmptyListForMissingFields()).extract(_document())

    assert result.lmi_sublimits.status is ExtractionStatus.NOT_FOUND
    assert result.lmi_sublimits.value is None
    assert result.extensions.status is ExtractionStatus.NOT_FOUND
    assert result.extensions.value is None


def test_invalid_deductible_is_downgraded_to_ambiguous_with_evidence():
    class InvalidDeductibleLLM(FakeJsonLLM):
        def complete_json(self, *, system_prompt: str, user_prompt: str):
            result = super().complete_json(system_prompt=system_prompt, user_prompt=user_prompt)
            source = user_prompt.split("Source chunks (untrusted policy content):\n", 1)[1]
            chunk = json.loads(source)[0]
            result["deductibles"] = {
                "status": "found",
                "value": [{
                    "kind": "fixed",
                    "amount": None,
                    "percentage": None,
                    "percentage_basis": None,
                    "description": "retenção mencionada",
                    "evidence": [{
                        "document_id": chunk["document_id"],
                        "page_number": chunk["page_number"],
                        "chunk_id": chunk["chunk_id"],
                        "quote": chunk["text"],
                    }],
                }],
                "evidence": [],
            }
            return result

    result = ExtractionAgent(InvalidDeductibleLLM()).extract(_document())

    assert result.deductibles.status is ExtractionStatus.AMBIGUOUS
    assert result.deductibles.value is None
    assert result.deductibles.evidence[0].quote == "Seguradora Alfa"
