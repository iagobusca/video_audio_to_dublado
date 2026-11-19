"""Configuracao global do projeto dubbr."""
from pathlib import Path
import os
import yaml

ROOT = Path(__file__).resolve().parents[2]
BIN_DIR = ROOT / "bin"
MODELS_DIR = ROOT / "modelos"
OUTPUT_DIR = ROOT / "saidas"
VOICES_DIR = ROOT / "vozes"
LOGS_DIR = ROOT / "logs"
CATALOGO = ROOT / "catalogo.yaml"
GLOSSARIO = ROOT / "glossario.yaml"
HF_HOME = MODELS_DIR / "hf"

# defaults
VRAM_BUDGET_GB = float(os.environ.get("VRAM_BUDGET_GB", "7.2"))
HOST = "127.0.0.1"
PORT = 7860
RESIDENT_MODE = os.environ.get("RESIDENT_MODE", "0") == "1"


def load_catalogo():
    with open(CATALOGO, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dirs():
    for d in (MODELS_DIR, OUTPUT_DIR, VOICES_DIR, LOGS_DIR, HF_HOME):
        d.mkdir(parents=True, exist_ok=True)


ensure_dirs()
os.environ.setdefault("HF_HOME", str(HF_HOME))
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
