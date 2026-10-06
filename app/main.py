"""InsurMinds — ponto de entrada da interface Streamlit (navegação por páginas)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

st.set_page_config(page_title="InsurMinds", page_icon="🛡️", layout="wide")

from app.ui import components as ui  # noqa: E402
from app.ui.llm_settings import render_model_settings  # noqa: E402
from app.ui.theme import inject_css  # noqa: E402
from app.views import analysis, history, results  # noqa: E402

inject_css()
ui.header()
st.session_state["llm"] = render_model_settings()

pages = {
    "analysis": st.Page(analysis.render, title="Nova análise", url_path="nova-analise",
                        icon=":material/upload_file:", default=True),
    "results": st.Page(results.render, title="Resultados", url_path="resultados",
                       icon=":material/compare_arrows:"),
    "history": st.Page(history.render, title="Histórico", url_path="historico",
                       icon=":material/history:"),
}
st.session_state["pages"] = pages
st.navigation(list(pages.values())).run()
