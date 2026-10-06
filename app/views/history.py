"""Página 'Histórico': análises guardadas neste dispositivo."""

import sqlite3
from pathlib import Path

import streamlit as st

from app.config import DATABASE_PATH
from src.database import SQLiteAnalysisRepository


def render() -> None:
    pages = st.session_state["pages"]
    st.header("Histórico local")
    st.caption("Análises guardadas neste dispositivo (só dados extraídos, sem os PDFs).")
    if not Path(DATABASE_PATH).exists():
        st.info(
            "Nenhuma análise guardada ainda. Marque “Guardar a análise no histórico local” "
            "ao analisar."
        )
        st.page_link(pages["analysis"], label="Ir para Nova análise", icon=":material/upload_file:")
        return
    try:
        repository = SQLiteAnalysisRepository(DATABASE_PATH)
        summaries = repository.list_recent()
    except (OSError, ValueError, sqlite3.Error):
        st.error("Não foi possível abrir o histórico local.")
        return
    if not summaries:
        st.info("Ainda não há análises guardadas.")
        return
    for item in summaries:
        with st.container(border=True):
            left, right = st.columns([5, 1])
            left.markdown(f"**#{item.analysis_id}** · {item.policy_a_name} × {item.policy_b_name}")
            if right.button("Abrir", key=f"open_{item.analysis_id}", use_container_width=True):
                stored = repository.get(item.analysis_id)
                if stored:
                    st.session_state["insurminds_policies"] = [stored.policy_a, stored.policy_b]
                    st.session_state["insurminds_report"] = stored.report
                    if stored.explanation:
                        st.session_state["insurminds_explanation"] = stored.explanation
                    else:
                        st.session_state.pop("insurminds_explanation", None)
                    st.switch_page(pages["results"])
