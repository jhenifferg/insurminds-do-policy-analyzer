"""Configuração compartilhada da interface."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/insurminds.sqlite3")
SAMPLE_DIR = ROOT / "data" / "samples"
SAMPLE_NAMES = ("Apolice_DO_Ficticia_A.pdf", "Apolice_DO_Ficticia_B.pdf")
