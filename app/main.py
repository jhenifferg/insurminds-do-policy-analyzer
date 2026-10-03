"""Streamlit MVP for evidence-backed D&O policy comparison."""

import csv
import importlib
import io
import mimetypes
import os
from pathlib import Path
import sqlite3

import streamlit as st

import src.comparison.engine as comparison_engine_module
import src.extraction.normalization as normalization_module
from src.comparison import ComparisonEngine
from src.database import SQLiteAnalysisRepository
from src.extraction import ExtractionAgent, ExplanationAgent
from src.ingestion import DocumentIngestionPipeline, DocumentInput
from src.llm import (
    GeminiGenerateContentClient,
    GeminiRequestError,
    OpenAIChatClient,
    OpenAIRequestError,
)


def _show_evidence(evidence_items) -> None:
    if not evidence_items:
        st.caption("Sem citação associada; requer revisão.")
        return
    for evidence in evidence_items:
        st.caption(f"Página {evidence.page_number} · chunk {evidence.chunk_id}")
        st.text(evidence.quote)


st.set_page_config(page_title="InsurMinds", page_icon="🛡️", layout="wide")
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/insurminds.sqlite3")
st.title("InsurMinds")
st.subheader("Análise e comparação de apólices D&O")
st.write(
    "Carregue duas apólices para extrair dados estruturados, comparar diferenças "
    "e consultar os trechos que sustentam cada resultado."
)
st.warning(
    "O texto extraído será enviado ao provedor selecionado quando iniciar a análise. "
    "Use apenas documentos cujo envio externo esteja autorizado. Os resultados "
    "são apoio à revisão e não substituem análise especializada."
)

with st.sidebar:
    st.header("Configuração do modelo")
    provider = st.selectbox(
        "Provedor de IA",
        ["Gemini", "OpenAI"],
        index=0 if os.getenv("LLM_PROVIDER", "Gemini").lower() == "gemini" else 1,
    )
    default_api_key = (
        os.getenv("GEMINI_API_KEY", os.getenv("LLM_API_KEY", ""))
        if provider == "Gemini"
        else os.getenv("OPENAI_API_KEY", os.getenv("LLM_API_KEY", ""))
    )
    api_key = st.text_input(
        f"Chave da API {provider}",
        value=default_api_key,
        type="password",
        help="A chave é usada apenas durante esta sessão e não é gravada no projeto.",
    )
    model = st.text_input(
        "Modelo",
        value=(
            os.getenv("GEMINI_MODEL", os.getenv("LLM_MODEL", "gemini-3.8-flash"))
            if provider == "Gemini"
            else os.getenv("OPENAI_MODEL", os.getenv("LLM_MODEL", ""))
        ),
        placeholder="Ex.: gemini-3.8-flash",
    )
    st.caption("Para Gemini, use uma chave do Google AI Studio e um modelo disponível na sua conta.")
    st.divider()
    st.header("Histórico local")
    if Path(DATABASE_PATH).exists():
        try:
            repository = SQLiteAnalysisRepository(DATABASE_PATH)
            summaries = repository.list_recent()
            if summaries:
                chosen = st.selectbox(
                    "Análises guardadas",
                    summaries,
                    format_func=lambda item: (
                        f"#{item.analysis_id} · {item.policy_a_name} × {item.policy_b_name}"
                    ),
                )
                if st.button("Abrir análise guardada"):
                    stored = repository.get(chosen.analysis_id)
                    if stored:
                        st.session_state["insurminds_policies"] = [
                            stored.policy_a, stored.policy_b
                        ]
                        st.session_state["insurminds_report"] = stored.report
                        if stored.explanation:
                            st.session_state["insurminds_explanation"] = stored.explanation
                        else:
                            st.session_state.pop("insurminds_explanation", None)
            else:
                st.caption("Ainda não há análises guardadas.")
        except (OSError, ValueError, sqlite3.Error):
            st.caption("Não foi possível abrir o histórico local.")
    else:
        st.caption("Nenhuma análise foi guardada neste dispositivo.")

uploads = st.file_uploader(
    "Selecione exatamente duas apólices",
    type=["pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=True,
    help="PDF, PNG ou JPEG. Os arquivos são processados em memória e não são salvos pelo app.",
)

st.checkbox(
    f"Confirmo que tenho autorização para enviar o texto destas apólices ao provedor selecionado ({provider}).",
    key="external_consent",
)
save_history = st.checkbox(
    "Guardar os dados extraídos e a comparação no histórico local deste dispositivo.",
    value=False,
)
run_analysis = st.button("Analisar e comparar", type="primary")

if run_analysis:
    st.session_state.pop("insurminds_policies", None)
    st.session_state.pop("insurminds_report", None)
    st.session_state.pop("insurminds_explanation", None)
    if not st.session_state.get("external_consent", False):
        st.error("Confirme a autorização de envio para iniciar esta análise.")
    elif len(uploads) != 2:
        st.error("Selecione exatamente duas apólices.")
    elif not api_key.strip() or not model.strip():
        st.error(f"Informe uma chave da API {provider} e o nome de um modelo habilitado.")
    else:
        if provider == "Gemini":
            client = GeminiGenerateContentClient(api_key, model)
        else:
            client = OpenAIChatClient(api_key, model)
        ingestion = DocumentIngestionPipeline()
        extractor = ExtractionAgent(client)
        policies = []
        try:
            progress = st.progress(0, text="A preparar documentos…")
            for index, upload in enumerate(uploads, start=1):
                media_type = upload.type or mimetypes.guess_type(upload.name)[0]
                if media_type not in {"application/pdf", "image/png", "image/jpeg"}:
                    raise ValueError(f"Formato não suportado: {upload.name}")
                doc_input = DocumentInput(
                    filename=upload.name,
                    media_type=media_type,
                    content=upload.getvalue(),
                )
                with st.spinner(f"A processar {upload.name}…"):
                    document = ingestion.process(doc_input)
                    policy = extractor.extract(document)
                policies.append(policy)
                progress.progress(index * 45, text=f"Documento {index}/2 extraído")

            report = ComparisonEngine().compare(policies[0], policies[1])
            st.session_state["insurminds_policies"] = policies
            st.session_state["insurminds_report"] = report
            st.session_state.pop("insurminds_explanation", None)
            if save_history:
                try:
                    analysis_id = SQLiteAnalysisRepository(DATABASE_PATH).save(
                        policies[0], policies[1], report
                    )
                    st.success(f"Análise guardada localmente com o número {analysis_id}.")
                except (OSError, ValueError, sqlite3.Error) as exc:
                    st.warning(f"A comparação foi concluída, mas não foi guardada: {exc}")
            progress.progress(100, text="Comparação concluída")
        except (ValueError, OpenAIRequestError, GeminiRequestError, OSError) as exc:
            st.error(f"Não foi possível concluir a análise: {exc}")
        except Exception:
            st.error(
                "Ocorreu um erro inesperado ao processar os documentos. "
                "Confira os formatos e tente novamente."
            )

if st.session_state.get("insurminds_policies") and st.button(
    "Recalcular comparação com os dados já extraídos",
    help="Atualiza as regras de comparação sem fazer outra chamada à API de IA.",
):
    # Streamlit may keep imported Python modules in memory after their source
    # files change. Reload the deterministic rules when the user explicitly
    # asks to recalculate, while preserving extracted policy data in session.
    importlib.invalidate_caches()
    importlib.reload(normalization_module)
    importlib.reload(comparison_engine_module)
    policies_to_recompare = st.session_state["insurminds_policies"]
    normalizer = normalization_module.ClauseNormalizer()
    for policy in policies_to_recompare:
        normalizer.normalize(policy)
    st.session_state["insurminds_report"] = comparison_engine_module.ComparisonEngine().compare(
        policies_to_recompare[0], policies_to_recompare[1]
    )
    st.session_state.pop("insurminds_explanation", None)
    st.success("Comparação atualizada sem chamar a API de IA.")

if "insurminds_report" in st.session_state:
    policies = st.session_state["insurminds_policies"]
    report = st.session_state["insurminds_report"]
    st.divider()
    st.header("Diferenças identificadas")
    st.caption(f"Apólice A: {policies[0].filename} · Apólice B: {policies[1].filename}")
    rows = [
        {
            "Critério": row.criterion,
            "Apólice A": row.policy_a,
            "Apólice B": row.policy_b,
            "Resultado": row.difference.value,
            "Leitura inicial": row.explanation,
        }
        for row in report.rows
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)

    csv_buffer = io.StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=list(rows[0]) if rows else [])
    if rows:
        writer.writeheader()
        writer.writerows(rows)
    st.download_button(
        "Baixar comparação CSV",
        data=csv_buffer.getvalue().encode("utf-8-sig"),
        file_name="insurminds_comparacao.csv",
        mime="text/csv",
        disabled=not rows,
    )

    with st.expander("Evidências por diferença"):
        for row in report.rows:
            st.markdown(f"**{row.criterion}**")
            left, right = st.columns(2)
            with left:
                st.caption("Apólice A")
                _show_evidence(row.evidence_policy_a)
            with right:
                st.caption("Apólice B")
                _show_evidence(row.evidence_policy_b)

    with st.expander("Dados estruturados extraídos"):
        for policy in policies:
            st.markdown(f"**{policy.filename}**")
            st.json(policy.model_dump(mode="json"))

    if st.button("Gerar explicação das diferenças"):
        try:
            with st.spinner("A gerar explicação baseada na comparação…"):
                explanation = ExplanationAgent(
                    GeminiGenerateContentClient(api_key, model)
                    if provider == "Gemini"
                    else OpenAIChatClient(api_key, model)
                ).explain(report)
            st.session_state["insurminds_explanation"] = explanation
        except (ValueError, OpenAIRequestError, GeminiRequestError) as exc:
            st.error(f"Não foi possível gerar a explicação: {exc}")
    if st.session_state.get("insurminds_explanation"):
        st.subheader("Explicação assistida por IA")
        st.write(st.session_state["insurminds_explanation"])
