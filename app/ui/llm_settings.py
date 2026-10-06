"""Configuração do provedor de IA (barra lateral): provedor, chave e modelo."""

import hashlib
import html
import os
from dataclasses import dataclass

import streamlit as st

from src.llm import GeminiGenerateContentClient, OpenAIChatClient
from src.llm.model_listing import ModelListError, list_models


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    api_key: str
    model: str

    @property
    def ready(self) -> bool:
        return bool(self.api_key.strip() and self.model.strip())


def make_client(config: LLMConfig):
    if config.provider == "Gemini":
        # 5 tentativas: o Gemini devolve 503 em picos de demanda.
        # Nos modelos 2.5 "flash" o raciocínio extra é desligado: a extração fica bem mais rápida.
        thinking = 0 if "2.5-flash" in config.model else None
        return GeminiGenerateContentClient(
            config.api_key, config.model, max_attempts=5,
            thinking_budget=thinking, thinking_level="low",
        )
    return OpenAIChatClient(config.api_key, config.model)


def _env_key(provider: str) -> str:
    if provider == "Gemini":
        return os.getenv("GEMINI_API_KEY", os.getenv("LLM_API_KEY", ""))
    return os.getenv("OPENAI_API_KEY", os.getenv("LLM_API_KEY", ""))


def _env_model(provider: str) -> str:
    if provider == "Gemini":
        return os.getenv("GEMINI_MODEL", os.getenv("LLM_MODEL", "gemini-3.8-flash"))
    return os.getenv("OPENAI_MODEL", os.getenv("LLM_MODEL", ""))


def _sync_model(provider: str) -> None:
    choice = st.session_state.get(f"sel_{provider}")
    if choice:
        st.session_state[f"model_{provider}"] = choice


def render_model_settings() -> LLMConfig:
    start = "Gemini" if os.getenv("LLM_PROVIDER", "Gemini").lower() == "gemini" else "OpenAI"
    env_ready = bool(_env_key(start).strip() and _env_model(start).strip())
    with st.sidebar:
        st.markdown('<div class="im-side-title">Modelo de IA</div>', unsafe_allow_html=True)
        status_slot = st.container()
        with st.expander("Configurar provedor, chave e modelo", expanded=not env_ready):
            provider = st.selectbox(
                "Provedor", ["Gemini", "OpenAI"], index=0 if start == "Gemini" else 1
            )
            env_key = _env_key(provider)
            source = "Digitar nesta tela"
            if env_key.strip():
                source = st.radio(
                    "Origem da chave", ["Arquivo .env", "Digitar nesta tela"],
                    horizontal=True, key=f"keysrc_{provider}",
                )
            if source == "Arquivo .env":
                api_key = env_key
                st.caption("Chave carregada do arquivo .env (não é exibida na tela).")
            else:
                api_key = st.text_input(
                    f"Chave da API {provider}", type="password", key=f"key_{provider}",
                    placeholder="Cole aqui a sua chave",
                    help="Fica só na memória desta sessão; não é gravada em arquivo.",
                )
                st.caption("A chave digitada vale apenas nesta sessão.")

            key_id = hashlib.sha256(api_key.encode()).hexdigest()[:10] if api_key.strip() else ""
            flag = f"autolist_{provider}_{key_id}"
            if key_id and not st.session_state.get(flag):
                st.session_state[flag] = True
                try:
                    with st.spinner("Buscando os modelos da sua conta…"):
                        found = list_models(provider, api_key, timeout=8)
                    if found:
                        st.session_state[f"models_{provider}"] = found
                except ModelListError:
                    st.session_state.pop(f"models_{provider}", None)

            model_key = f"model_{provider}"
            st.session_state.setdefault(model_key, _env_model(provider))
            current = st.session_state[model_key]
            listed = st.session_state.get(f"models_{provider}")
            if listed:
                options = listed if current in listed or not current.strip() else [current] + listed
                model = st.selectbox(
                    f"Modelo ({len(listed)} disponíveis)", options,
                    index=options.index(current) if current in options else 0,
                    key=f"sel_{provider}", on_change=_sync_model, args=(provider,),
                )
            else:
                model = st.text_input(
                    "Modelo", value=current, key=f"txt_{provider}",
                    placeholder="Ex.: gemini-2.5-flash",
                    help="Não foi possível listar os modelos automaticamente; digite o nome.",
                )
            st.session_state[model_key] = model
            if st.button(
                "Atualizar lista de modelos" if listed else "Tentar listar modelos de novo",
                use_container_width=True, disabled=not api_key.strip(),
            ):
                try:
                    with st.spinner("Consultando o provedor…"):
                        found = list_models(provider, api_key)
                    if found:
                        st.session_state[f"models_{provider}"] = found
                        st.rerun()
                    st.warning("Nenhum modelo de texto encontrado para esta chave.")
                except ModelListError as exc:
                    st.session_state.pop(f"models_{provider}", None)
                    st.error(str(exc))

        config = LLMConfig(provider, api_key, model)
        key_ok, model_ok = bool(api_key.strip()), bool(model.strip())
        if config.ready:
            state = '<span class="dot ok"></span>Pronto para analisar'
        else:
            missing = " e ".join(n for n, ok in (("chave", key_ok), ("modelo", model_ok)) if not ok)
            state = f'<span class="dot no"></span>Falta informar: {missing}'
        with status_slot:
            st.markdown(
                f'<div class="im-llm"><div class="p">{html.escape(provider)}</div>'
                f'<div class="m">{html.escape(model.strip() or "modelo não definido")}</div>'
                f'<div class="s">{state}</div></div>',
                unsafe_allow_html=True,
            )
    return config
