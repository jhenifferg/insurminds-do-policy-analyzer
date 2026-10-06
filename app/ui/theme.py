"""Tema visual (CSS) do InsurMinds."""

import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap');
html, body, [class*="css"], .stApp {font-family:'IBM Plex Sans', system-ui, sans-serif;}
#MainMenu, footer, [data-testid="stToolbar"] {visibility:hidden;}
header[data-testid="stHeader"] {background:transparent; height:2.2rem;}
.stApp {background:#f4f6f8;}
.block-container {max-width:1120px; padding-top:3.4rem; padding-bottom:3rem;}
[data-testid="stSidebar"] {background:#fff; border-right:1px solid #d9e0e7;}
[data-testid="stSidebar"] h2 {font-size:.8rem !important; font-weight:600 !important; color:#5d6b79; text-transform:none; letter-spacing:.02em; padding:0 0 .2rem;}
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {padding-top:1.6rem;}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {gap:.65rem;}
[data-testid="stSidebar"] hr {margin:.6rem 0;}
h1, h2, h3 {color:#16222f; letter-spacing:-0.01em;}
h2 {font-size:1.25rem !important; font-weight:600 !important;}
.im-bar {display:flex; align-items:center; gap:14px; padding:2px 0 16px; border-bottom:1px solid #d9e0e7; margin-bottom:20px;}
.im-mark {width:38px; height:38px; border-radius:8px; background:#16222f; color:#fff; display:flex; align-items:center; justify-content:center; font-weight:600; font-size:.95rem; letter-spacing:.02em;}
.im-bar .brand {font-size:1.5rem; font-weight:600; color:#16222f; line-height:1.1;}
.im-bar .tag {color:#5d6b79; font-size:.92rem; margin-top:2px;}
.im-bar .pill {margin-left:auto; font-size:.78rem; color:#17607f; background:#eaf4f8; border:1px solid #c6dfe8; padding:4px 11px; border-radius:999px; white-space:nowrap;}
.im-side-title {font-size:.8rem; font-weight:600; color:#5d6b79; letter-spacing:.02em; margin:0 0 6px;}
.im-llm {border:1px solid #d9e0e7; border-radius:8px; padding:12px 14px; background:#fff;}
.im-llm .m {font-weight:600; color:#16222f; font-size:.95rem; word-break:break-all;}
.im-llm .p {color:#5d6b79; font-size:.8rem;}
.im-llm .s {display:flex; gap:8px; align-items:center; margin-top:8px; font-size:.84rem; color:#16222f;}
.im-llm .dot {width:9px; height:9px; border-radius:50%; flex:none;}
.im-llm .dot.ok {background:#3a7a52;}
.im-llm .dot.no {background:#a96a12;}
.im-sec {font-weight:600; color:#16222f; font-size:1rem; margin:0 0 4px;}
.im-sec span {display:block; font-weight:400; color:#5d6b79; font-size:.84rem; margin-top:2px;}
[data-testid="stVerticalBlockBorderWrapper"] {background:#fff; border-color:#d9e0e7 !important; border-radius:8px !important;}
.stButton > button[kind="primary"]:disabled {background:#e3e8ec !important; border-color:#e3e8ec !important; color:#8693a0 !important; cursor:not-allowed;}
.stButton > button[kind="primary"] {height:3rem; font-size:1rem;}
.im-steps {display:flex; gap:0; margin:0 0 18px; border:1px solid #d9e0e7; border-radius:6px; background:#fff; overflow:hidden;}
.im-step {flex:1; display:flex; gap:12px; align-items:center; padding:12px 16px; color:#5d6b79; font-size:.88rem; border-right:1px solid #d9e0e7;}
.im-step:last-child {border-right:0;}
.im-step .n {width:26px; height:26px; flex:none; border-radius:50%; border:1.5px solid #b8c3cd; display:flex; align-items:center; justify-content:center; font-weight:600; font-size:.85rem;}
.im-step b {display:block; color:#16222f; font-size:.95rem;}
.im-step.on {background:#f0f7fa;}
.im-step.on .n {background:#17607f; border-color:#17607f; color:#fff;}
.im-step.done .n {background:#3a7a52; border-color:#3a7a52; color:#fff;}
.im-notice {border-left:4px solid #a96a12; background:#fff8ea; padding:10px 14px; font-size:.88rem; color:#4a3b1c; margin-bottom:16px; border-radius:0 4px 4px 0;}
[data-testid="stFileUploader"] section {background:#fff; border:1.5px dashed #b8c3cd; border-radius:6px;}
[data-testid="stMetric"] {background:#fff; border:1px solid #d9e0e7; border-radius:6px; padding:14px 16px;}
[data-testid="stMetricLabel"] {color:#5d6b79;}
[data-testid="stMetricValue"] {color:#16222f; font-weight:600;}
.stButton > button[kind="primary"] {background:#17607f; border-color:#17607f; font-weight:500; border-radius:4px;}
.stButton > button[kind="primary"]:hover {background:#124d66; border-color:#124d66;}
.stButton > button, .stDownloadButton > button {border-radius:4px;}
div[role="radiogroup"] {gap:4px; border-bottom:1px solid #d9e0e7; padding-bottom:4px;}
.im-tblwrap {overflow-x:auto; background:#fff; border:1px solid #d9e0e7; border-radius:6px; margin:8px 0 14px;}
.im-tbl {width:100%; border-collapse:collapse; font-size:.92rem;}
.im-tbl th {text-align:left; font-weight:600; color:#5d6b79; font-size:.82rem; padding:10px 14px; border-bottom:1px solid #d9e0e7; background:#fafbfc;}
.im-tbl td {padding:12px 14px; border-bottom:1px solid #edf1f4; vertical-align:top; color:#16222f;}
.im-tbl tr:last-child td {border-bottom:0;}
.im-tbl td.c {font-weight:500; min-width:180px;}
.im-tbl td.x {color:#5d6b79; min-width:200px;}
.im-badge {display:inline-block; padding:3px 10px; border-radius:999px; font-size:.8rem; font-weight:500; white-space:nowrap; border:1px solid;}
.im-badge.info {color:#2f5d9e; background:#eef3fb; border-color:#c5d5ee;}
.im-badge.ok {color:#2f6a45; background:#eef7f1; border-color:#c4e0cf;}
.im-badge.warn {color:#8a560a; background:#fdf4e3; border-color:#ecd5a6;}
.im-badge.alert {color:#9a3720; background:#fcefeb; border-color:#efc4b8;}
.im-badge.mute {color:#56626e; background:#f0f2f4; border-color:#d3d9de;}
.im-hl {background:#fff; border:1px solid #d9e0e7; border-radius:8px; padding:14px 16px; height:100%;}
.im-hl .t {font-weight:600; color:#16222f; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center; gap:8px;}
.im-hl .v {display:grid; grid-template-columns:1fr 1fr; gap:14px;}
.im-hl small {display:block; color:#5d6b79; font-size:.78rem;}
.im-hl .n {font-size:1.15rem; font-weight:600; color:#16222f; word-break:break-word;}
.im-quote {border-left:3px solid #17607f; background:#fff; padding:8px 12px; margin:0 0 8px; font-size:.9rem; border-radius:0 4px 4px 0;}
.im-quote small {display:block; color:#5d6b79; font-size:.78rem; margin-bottom:2px;}
.im-quote.none {border-color:#b0432a; color:#5d6b79;}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
