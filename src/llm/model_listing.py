"""Lista os modelos de texto disponíveis para uma chave de API (somente biblioteca padrão)."""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models?pageSize=1000"
OPENAI_URL = "https://api.openai.com/v1/models"
GROQ_URL = "https://api.groq.com/openai/v1/models"
# Modelos Gemini que não servem para extrair texto (imagem, voz, vídeo, embeddings).
_GEMINI_EXCLUDE = (
    "image", "imagen", "tts", "audio", "live", "embedding", "veo",
    "robotics", "computer-use", "learnlm", "aqa",
)
_OPENAI_PREFIXES = ("gpt", "o1", "o3", "o4", "chatgpt")
_OPENAI_EXCLUDE = (
    "embedding", "whisper", "tts", "audio", "image", "realtime",
    "transcribe", "moderation", "search", "dall",
)
_GROQ_EXCLUDE = (
    "whisper", "guard", "safety", "tts", "transcribe", "audio",
    "compound", "playai",
)


class ModelListError(RuntimeError):
    """Erro ao consultar os modelos; a mensagem nunca contém a chave."""


def _get_json(url: str, headers: dict, timeout: int) -> dict:
    try:
        with urlopen(Request(url, headers=headers), timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        hint = " Verifique a chave de API." if exc.code in (400, 401, 403) else ""
        raise ModelListError(f"O provedor respondeu HTTP {exc.code}.{hint}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise ModelListError("Não foi possível conectar ao provedor.") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ModelListError("Resposta inválida do provedor.") from exc


def list_gemini_models(api_key: str, timeout: int = 20) -> list[str]:
    data = _get_json(GEMINI_URL, {"x-goog-api-key": api_key.strip()}, timeout)
    names = []
    for item in data.get("models", []):
        if "generateContent" not in item.get("supportedGenerationMethods", []):
            continue
        name = str(item.get("name", "")).removeprefix("models/")
        if name.startswith("gemini") and not any(w in name for w in _GEMINI_EXCLUDE):
            names.append(name)
    return sorted(set(names))


def list_openai_models(api_key: str, timeout: int = 20) -> list[str]:
    data = _get_json(OPENAI_URL, {"Authorization": f"Bearer {api_key.strip()}"}, timeout)
    names = [
        str(item.get("id", ""))
        for item in data.get("data", [])
        if str(item.get("id", "")).startswith(_OPENAI_PREFIXES)
        and not any(word in str(item.get("id", "")) for word in _OPENAI_EXCLUDE)
    ]
    return sorted(set(names))


def list_groq_models(api_key: str, timeout: int = 20) -> list[str]:
    """List text models available to a Groq API key."""
    data = _get_json(
        GROQ_URL,
        {"Authorization": f"Bearer {api_key.strip()}"},
        timeout,
    )
    names = [
        str(item.get("id", ""))
        for item in data.get("data", [])
        if str(item.get("id", ""))
        and not any(word in str(item.get("id", "")).lower() for word in _GROQ_EXCLUDE)
    ]
    return sorted(set(names))


def list_models(provider: str, api_key: str, timeout: int = 20) -> list[str]:
    if not api_key.strip():
        raise ModelListError("Informe a chave de API para listar os modelos.")
    if provider == "Gemini":
        return list_gemini_models(api_key, timeout)
    if provider == "Groq":
        return list_groq_models(api_key, timeout)
    return list_openai_models(api_key, timeout)


__all__ = [
    "ModelListError", "list_models", "list_gemini_models",
    "list_groq_models", "list_openai_models",
]
