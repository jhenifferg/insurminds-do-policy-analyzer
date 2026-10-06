"""Página 'Nova análise': carregar as apólices, autorizar o envio e analisar."""

import hashlib
import mimetypes
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import streamlit as st

from app.config import DATABASE_PATH, SAMPLE_DIR, SAMPLE_NAMES
from app.ui import components as ui
from app.ui.llm_settings import make_client
from src.comparison import ComparisonEngine
from src.database import SQLiteAnalysisRepository
from src.extraction import ExtractionAgent
from src.ingestion import DocumentIngestionPipeline, DocumentInput
from src.llm import GeminiRequestError, OpenAIRequestError

TYPES = ["pdf", "png", "jpg", "jpeg"]


class SampleFile:
    """Arquivo de exemplo com a interface mínima de um upload do Streamlit."""

    type = "application/pdf"

    def __init__(self, path: Path) -> None:
        self.name = path.name
        self._content = path.read_bytes()

    def getvalue(self) -> bytes:
        return self._content


def _documents_block() -> list:
    with st.container(border=True):
        ui.section_title(
            "Documentos",
            "PDF, PNG ou JPEG, até 200 MB por arquivo. Processados em memória, sem salvar o arquivo.",
        )
        samples_ok = all((SAMPLE_DIR / name).exists() for name in SAMPLE_NAMES)
        use_samples = st.checkbox(
            "Usar as apólices de exemplo (fictícias)", key="use_samples",
            disabled=not samples_ok,
            help="Carrega as duas apólices de data/samples, para testar sem enviar arquivos.",
        )
        col_a, col_b = st.columns(2)
        if use_samples and samples_ok:
            files = [SampleFile(SAMPLE_DIR / name) for name in SAMPLE_NAMES]
            col_a.success(f"Apólice A: {files[0].name}")
            col_b.success(f"Apólice B: {files[1].name}")
            return files
        with col_a:
            upload_a = st.file_uploader("Apólice A", type=TYPES, key="upload_a")
        with col_b:
            upload_b = st.file_uploader("Apólice B", type=TYPES, key="upload_b")
        return [item for item in (upload_a, upload_b) if item is not None]


def _ingest_and_extract(name: str, media_type: str, content: bytes, config):
    """Roda em thread: lê o documento e extrai os campos (sem chamadas à interface)."""
    t0 = time.perf_counter()
    document = DocumentIngestionPipeline().process(
        DocumentInput(filename=name, media_type=media_type, content=content)
    )
    t1 = time.perf_counter()
    client = make_client(config)
    policy = ExtractionAgent(client, max_workers=3).extract(document)
    t2 = time.perf_counter()
    return policy, t1 - t0, t2 - t1, getattr(client, "retries", 0)


def _run(uploads, config, save_history: bool) -> bool:
    """Executa a análise. Devolve True quando terminou com sucesso."""
    for key in ("insurminds_policies", "insurminds_report", "insurminds_explanation"):
        st.session_state.pop(key, None)
    cache = st.session_state.setdefault("_extract_cache", {})
    started = time.perf_counter()
    with st.status("Analisando as apólices…", expanded=True) as status:
        try:
            items = []
            for upload in uploads:
                media_type = upload.type or mimetypes.guess_type(upload.name)[0]
                if media_type not in {"application/pdf", "image/png", "image/jpeg"}:
                    raise ValueError(f"Formato não suportado: {upload.name}")
                content = upload.getvalue()
                key = f"{hashlib.sha256(content).hexdigest()}|{config.provider}|{config.model}"
                items.append((upload.name, media_type, content, key))

            policies = [None] * len(items)
            pending = {}
            with ThreadPoolExecutor(max_workers=len(items)) as pool:
                for index, (name, media_type, content, key) in enumerate(items):
                    label = "AB"[index]
                    if key in cache:
                        policies[index] = cache[key]
                        st.write(f"Apólice {label}: resultado reaproveitado (mesmo arquivo e modelo).")
                    else:
                        pending[pool.submit(_ingest_and_extract, name, media_type, content, config)] = index
                if pending:
                    st.write("Lendo e extraindo as duas apólices ao mesmo tempo…")
                for future in as_completed(pending):
                    index = pending[future]
                    policy, read_s, ai_s, retries = future.result()
                    policies[index] = policy
                    cache[items[index][3]] = policy
                    retry_note = f" · {retries} nova(s) tentativa(s) por alta demanda" if retries else ""
                    st.write(
                        f"Apólice {'AB'[index]}: leitura {read_s:.1f} s · IA {ai_s:.1f} s{retry_note}"
                    )

            st.write("Comparando as apólices…")
            report = ComparisonEngine().compare(policies[0], policies[1])
            st.session_state["insurminds_policies"] = policies
            st.session_state["insurminds_report"] = report
            if save_history:
                try:
                    analysis_id = SQLiteAnalysisRepository(DATABASE_PATH).save(
                        policies[0], policies[1], report
                    )
                    st.write(f"Análise guardada localmente (nº {analysis_id}).")
                except (OSError, ValueError, sqlite3.Error) as exc:
                    st.warning(f"A comparação foi concluída, mas não foi guardada: {exc}")
            seconds = time.perf_counter() - started
            status.update(label=f"Comparação concluída em {seconds:.0f} s", state="complete", expanded=False)
            return True
        except (ValueError, OpenAIRequestError, GeminiRequestError, OSError) as exc:
            status.update(label="Não foi possível concluir a análise", state="error")
            st.error(f"Não foi possível concluir a análise: {exc}")
            if "429" in str(exc):
                st.info(
                    "A cota deste modelo foi excedida ou não está liberada na sua conta. "
                    "Na barra lateral, escolha um modelo de texto (um \"flash\" sem \"image\" "
                    "no nome) ou aguarde a cota renovar."
                )
            if "503" in str(exc):
                st.info(
                    "O Gemini está com alta demanda (o app já tentou 5 vezes). Aguarde um ou "
                    "dois minutos e tente de novo, ou troque o modelo na barra lateral."
                )
        except Exception:
            status.update(label="Erro inesperado", state="error")
            st.error(
                "Ocorreu um erro inesperado ao processar os documentos. "
                "Confira os formatos e tente novamente."
            )
    return False


def render() -> None:
    config = st.session_state["llm"]
    docs_ready = st.session_state.get("use_samples") or (
        st.session_state.get("upload_a") and st.session_state.get("upload_b")
    )
    ui.steps(2 if docs_ready else 1)
    ui.notice(
        "O texto extraído é enviado ao provedor de IA escolhido. Use apenas documentos "
        "cujo envio externo esteja autorizado. Os resultados apoiam a revisão e não "
        "substituem análise especializada."
    )
    uploads = _documents_block()

    with st.container(border=True):
        ui.section_title("Autorização e análise")
        left, right = st.columns([3, 2])
        with left:
            st.checkbox(
                f"Confirmo que tenho autorização para enviar o texto destas apólices ao provedor ({config.provider}).",
                key="external_consent",
            )
        with right:
            save_history = st.checkbox(
                "Guardar a análise no histórico local", value=False,
                help="Salva só dados extraídos e a comparação, não os PDFs.",
            )
        missing = []
        if len(uploads) != 2:
            missing.append("as duas apólices")
        elif uploads[0].getvalue() == uploads[1].getvalue():
            missing.append("dois arquivos diferentes (A e B são o mesmo documento)")
        if not st.session_state.get("external_consent", False):
            missing.append("a confirmação de autorização")
        if not config.ready:
            missing.append("chave e modelo na barra lateral")
        run = st.button(
            "Analisar e comparar", type="primary", disabled=bool(missing),
            use_container_width=True,
        )
        if missing:
            st.caption("Para começar, falta: " + ", ".join(missing) + ".")

    if run and _run(uploads, config, save_history):
        st.switch_page(st.session_state["pages"]["results"])
