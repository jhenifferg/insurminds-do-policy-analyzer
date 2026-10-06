"""Gera o ZIP de entrega sem credenciais e aborta se encontrar uma chave de API.

Uso (na raiz do projeto):  python scripts/build_delivery_zip.py
Saída: ../insurminds_entrega.zip (fora da pasta do projeto).
"""

import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT.parent / "insurminds_entrega.zip"

EXCLUDED_DIRS = {".venv", "venv", ".git", "__pycache__", ".pytest_cache", ".idea", ".vscode"}
EXCLUDED_NAMES = {".env", ".DS_Store", "secrets.toml"}
EXCLUDED_SUFFIXES = {".pyc", ".sqlite", ".sqlite3", ".db", ".log", ".pem", ".key"}
KEEP_ALWAYS = {".env.example"}

SECRET_PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z_\-]{30,}"),           # chaves Google/Gemini
    re.compile(r"sk-[A-Za-z0-9_\-]{20,}"),             # chaves OpenAI
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]
TEXT_SUFFIXES = {".py", ".md", ".txt", ".env", ".example", ".toml", ".json", ".yml", ".yaml", ".cfg", ".ini", ".jsx", ".js", ""}


def included_files():
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if path.name in KEEP_ALWAYS:
            yield path
            continue
        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        if path.name in EXCLUDED_NAMES or path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        if path.name.startswith(".env."):
            continue
        yield path


def find_secrets(files):
    found = []
    for path in files:
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                found.append(path.relative_to(ROOT))
                break
    return found


def main() -> int:
    files = list(included_files())
    leaks = find_secrets(files)
    if leaks:
        print("ERRO: possível chave de API encontrada. ZIP NÃO gerado.")
        for item in leaks:
            print(f"  - {item}")
        print("Remova a chave desses arquivos (e revogue-a no provedor) e tente de novo.")
        return 1
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, Path(ROOT.name) / path.relative_to(ROOT))
    print(f"ZIP gerado: {OUTPUT}  ({len(files)} arquivos)")
    print("Verificado: sem .env, .venv, .git, bancos locais ou chaves de API.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
