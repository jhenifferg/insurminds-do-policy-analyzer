"""Componentes visuais reutilizáveis."""

import html

import streamlit as st

from app.ui.labels import STATUS, TONE, pt, short


def header() -> None:
    st.markdown(
        '<div class="im-bar"><div class="im-mark">IM</div>'
        '<div><div class="brand">InsurMinds</div>'
        '<div class="tag">Análise e comparação de apólices D&amp;O, com a fonte de cada resultado</div></div>'
        '<span class="pill">Projeto Final I2A2</span></div>',
        unsafe_allow_html=True,
    )


def steps(stage: int) -> None:
    items = [
        ("Carregar", "Escolha as apólices A e B"),
        ("Analisar", "Autorize e inicie a análise"),
        ("Resultados", "Diferenças e evidências"),
    ]
    markup = ""
    for number, (title, subtitle) in enumerate(items, start=1):
        css = "done" if number < stage else "on" if number == stage else ""
        mark = "&#10003;" if number < stage else str(number)
        markup += (
            f'<div class="im-step {css}"><span class="n">{mark}</span>'
            f"<div><b>{title}</b>{subtitle}</div></div>"
        )
    st.markdown(f'<div class="im-steps">{markup}</div>', unsafe_allow_html=True)


def notice(text: str) -> None:
    st.markdown(f'<div class="im-notice">{html.escape(text)}</div>', unsafe_allow_html=True)


def section_title(title: str, subtitle: str = "") -> None:
    extra = f"<span>{html.escape(subtitle)}</span>" if subtitle else ""
    st.markdown(f'<div class="im-sec">{html.escape(title)}{extra}</div>', unsafe_allow_html=True)


def badge(kind: str) -> str:
    return (
        f'<span class="im-badge {TONE.get(kind, "mute")}">'
        f"{html.escape(STATUS.get(kind, kind))}</span>"
    )


def highlight_card(row) -> str:
    return (
        '<div class="im-hl"><div class="t">'
        f"<span>{html.escape(row.criterion)}</span>{badge(row.difference.value)}</div>"
        '<div class="v">'
        f'<div><small>Apólice A</small><div class="n">{html.escape(short(row.policy_a))}</div></div>'
        f'<div><small>Apólice B</small><div class="n">{html.escape(short(row.policy_b))}</div></div>'
        "</div></div>"
    )


def comparison_table(rows) -> None:
    body = ""
    for row in rows:
        body += (
            f'<tr><td class="c">{html.escape(row.criterion)}</td>'
            f"<td>{html.escape(pt(row.policy_a))}</td><td>{html.escape(pt(row.policy_b))}</td>"
            f"<td>{badge(row.difference.value)}</td>"
            f'<td class="x">{html.escape(row.explanation)}</td></tr>'
        )
    st.markdown(
        '<div class="im-tblwrap"><table class="im-tbl"><thead><tr>'
        "<th>Critério</th><th>Apólice A</th><th>Apólice B</th>"
        "<th>Resultado</th><th>Leitura inicial</th></tr></thead>"
        f"<tbody>{body}</tbody></table></div>",
        unsafe_allow_html=True,
    )


def evidence(items) -> None:
    if not items:
        st.caption("Sem citação associada; requer revisão.")
        return
    for item in items:
        st.markdown(
            f'<div class="im-quote"><small>Página {item.page_number} · '
            f"trecho {html.escape(str(item.chunk_id))}</small>"
            f"{html.escape(item.quote)}</div>",
            unsafe_allow_html=True,
        )
