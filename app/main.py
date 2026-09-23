"""Initial InsurMinds interface. Processing will be integrated later."""
import streamlit as st

st.set_page_config(page_title="InsurMinds", page_icon="🛡️", layout="wide")
st.title("InsurMinds")
st.subheader("Análise e comparação de apólices D&O")
st.info("Estrutura inicial do projeto. Extração e comparação ainda não implementadas.")
st.markdown("Fluxo previsto: documentos → texto/OCR → dados estruturados → comparação com evidências.")
