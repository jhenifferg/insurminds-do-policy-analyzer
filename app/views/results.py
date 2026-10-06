"""Página 'Resultados': resumo, comparação, evidências, dados e explicação."""

import csv
import importlib
import io

import streamlit as st

import src.comparison.engine as comparison_engine_module
import src.extraction.normalization as normalization_module
from app.ui import components as ui
from app.ui.labels import CATEGORIES, STATUS, category_of, pt
from app.ui.llm_settings import make_client
from src.extraction import ExplanationAgent
from src.llm import GeminiRequestError, OpenAIRequestError

VIEWS = ["Comparação", "Evidências", "Dados extraídos", "Explicação"]


def _recalculate(policies) -> None:
    # Recarrega as regras determinísticas sem chamar a IA de novo.
    importlib.invalidate_caches()
    importlib.reload(normalization_module)
    importlib.reload(comparison_engine_module)
    normalizer = normalization_module.ClauseNormalizer()
    for policy in policies:
        normalizer.normalize(policy)
    st.session_state["insurminds_report"] = comparison_engine_module.ComparisonEngine().compare(
        policies[0], policies[1]
    )
    st.session_state.pop("insurminds_explanation", None)


def _csv_bytes(rows) -> bytes:
    data = [
        {
            "Critério": row.criterion, "Apólice A": pt(row.policy_a), "Apólice B": pt(row.policy_b),
            "Resultado": STATUS.get(row.difference.value, row.difference.value),
            "Leitura inicial": row.explanation,
        }
        for row in rows
    ]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(data[0]) if data else [])
    if data:
        writer.writeheader()
        writer.writerows(data)
    return buffer.getvalue().encode("utf-8-sig")


def _comparison_view(rows) -> None:
    left, right = st.columns([2, 3])
    with left:
        category = st.selectbox("Categoria", CATEGORIES)
    with right:
        kinds = st.multiselect(
            "Resultado", list(STATUS), default=list(STATUS), format_func=lambda k: STATUS[k]
        )
    shown = [
        row for row in rows
        if row.difference.value in kinds
        and (category == "Todas" or category_of(row.criterion) == category)
    ]
    if shown:
        ui.comparison_table(shown)
    else:
        st.caption("Nenhum critério neste filtro.")
    st.download_button(
        "Baixar comparação (CSV)", data=_csv_bytes(rows), file_name="insurminds_comparacao.csv",
        mime="text/csv", disabled=not rows,
    )


def _evidence_view(rows) -> None:
    st.caption("Trecho do documento que sustenta cada resultado. Abra o critério desejado.")
    for row in rows:
        with st.expander(f"{STATUS.get(row.difference.value, row.difference.value)} · {row.criterion}"):
            st.write(row.explanation)
            left, right = st.columns(2)
            with left:
                st.markdown("**Apólice A**")
                ui.evidence(row.evidence_policy_a)
            with right:
                st.markdown("**Apólice B**")
                ui.evidence(row.evidence_policy_b)


def _explanation_view(report) -> None:
    config = st.session_state["llm"]
    text = st.session_state.get("insurminds_explanation")
    if text:
        st.subheader("Explicação assistida por IA")
        st.write(text)
        st.caption("Baseada apenas no relatório comparativo; não indica qual apólice é melhor.")
        return
    st.write("Gere um resumo em linguagem simples das diferenças encontradas.")
    if st.button("Gerar explicação das diferenças"):
        if not config.ready:
            st.error("Informe a chave e o modelo na barra lateral.")
            return
        try:
            with st.spinner("Gerando explicação baseada na comparação…"):
                st.session_state["insurminds_explanation"] = ExplanationAgent(
                    make_client(config)
                ).explain(report)
            st.rerun()
        except (ValueError, OpenAIRequestError, GeminiRequestError) as exc:
            st.error(f"Não foi possível gerar a explicação: {exc}")


def render() -> None:
    pages = st.session_state["pages"]
    report = st.session_state.get("insurminds_report")
    if report is None:
        st.info("Nenhuma análise para mostrar ainda.")
        st.page_link(pages["analysis"], label="Ir para Nova análise", icon=":material/upload_file:")
        return

    policies = st.session_state["insurminds_policies"]
    rows = report.rows
    ui.steps(3)

    head, actions = st.columns([4, 2])
    with head:
        st.header("Resultados")
        st.caption(f"**A:** {policies[0].filename}  ·  **B:** {policies[1].filename}")
    with actions:
        if st.button("Recalcular sem chamar a IA", use_container_width=True,
                     help="Reaplica as regras de comparação aos dados já extraídos."):
            _recalculate(policies)
            st.rerun()
        st.page_link(pages["analysis"], label="Nova análise", icon=":material/upload_file:")

    kinds = [row.difference.value for row in rows]
    review = kinds.count("needs_review") + kinds.count("not_comparable")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Critérios comparados", len(kinds))
    m2.metric("Iguais", kinds.count("equal"))
    m3.metric("Diferenças", sum(kinds.count(k) for k in ("higher", "lower", "different")))
    m4.metric("Para revisar", review)
    if review:
        st.info(
            "Itens “Revisar” ou “Não comparável” não significam ausência de cobertura: "
            "o dado não foi localizado ou exige análise especializada."
        )

    highlights = [
        row for row in rows if row.criterion.startswith(("Limite Máximo de Garantia", "Franquia"))
    ][:2]
    if highlights:
        st.markdown("**Principais condições**")
        for column, row in zip(st.columns(len(highlights)), highlights):
            column.markdown(ui.highlight_card(row), unsafe_allow_html=True)

    view = st.radio("Visualização", VIEWS, horizontal=True, key="view", label_visibility="collapsed")
    if view == "Comparação":
        _comparison_view(rows)
    elif view == "Evidências":
        _evidence_view(rows)
    elif view == "Dados extraídos":
        for policy in policies:
            with st.expander(policy.filename):
                st.json(policy.model_dump(mode="json"))
    else:
        _explanation_view(report)
