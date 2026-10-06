"""Configuração do provedor de IA (barra lateral): provedor, chave e modelo."""

import html
import os
from dataclasses import dataclass

import streamlit as st

from src.llm import (
    FallbackChatClient,
    GeminiGenerateContentClient,
    GroqChatClient,
    OpenAIChatClient,
)
DEFAULT_PROVIDER = "Gemini"


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
        primary = GeminiGenerateContentClient(
            config.api_key, config.model, max_attempts=5,
            thinking_budget=thinking, thinking_level="low",
        )
        fallback_key = os.getenv("GROQ_API_KEY", "").strip()
        # Mantém compatibilidade com o .env atual, que usa LLM_API_KEY para a
        # chave Groq enquanto LLM_PROVIDER/LLM_MODEL continuam apontando para Gemini.
        generic_key = os.getenv("LLM_API_KEY", "").strip()
        if not fallback_key and generic_key.startswith("gsk_"):
            fallback_key = generic_key
        if fallback_key:
            fallback_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip()
            return FallbackChatClient(
                primary,
                GroqChatClient(fallback_key, fallback_model),
            )
        return primary
    if config.provider == "Groq":
        return GroqChatClient(config.api_key, config.model)
    return OpenAIChatClient(config.api_key, config.model)


def _env_key(provider: str) -> str:
    if provider == "Gemini":
        return os.getenv("GEMINI_API_KEY", os.getenv("LLM_API_KEY", ""))
    if provider == "Groq":
        return os.getenv(
            "GROQ_API_KEY",
            os.getenv("LLM_API_KEY", ""),
        )
    return os.getenv("OPENAI_API_KEY", os.getenv("LLM_API_KEY", ""))


def _env_model(provider: str) -> str:
    if provider == "Gemini":
        return os.getenv("GEMINI_MODEL", os.getenv("LLM_MODEL", "gemini-3.1-flash-lite"))
    if provider == "Groq":
        configured_provider = os.getenv("LLM_PROVIDER", "").strip().lower()
        if configured_provider == "groq" and os.getenv("LLM_MODEL", "").strip():
            return os.environ["LLM_MODEL"]
        return os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    return os.getenv("OPENAI_MODEL", os.getenv("LLM_MODEL", ""))


def render_model_settings() -> LLMConfig:
    configured = os.getenv("LLM_PROVIDER", DEFAULT_PROVIDER).strip().lower()
    provider = DEFAULT_PROVIDER if configured not in {"gemini", "groq", "openai"} else configured.title()
    api_key = _env_key(provider)
    model = _env_model(provider)
    with st.sidebar:
        st.markdown('<div class="im-side-title">Modelo de IA</div>', unsafe_allow_html=True)
        status_slot = st.container()
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
