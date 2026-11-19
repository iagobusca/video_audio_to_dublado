"""tools/check_ui_tree.py - criterio de aceite automatizado (sem navegador).
Uso: python tools/check_ui_tree.py  (a partir da raiz do repo, com venv ativo)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from app import demo

cfg = demo.get_config_file() if hasattr(demo, "get_config_file") else None
if cfg is None:
    # fallback: tentar atributo config
    cfg = getattr(demo, "config", None)
if cfg is None:
    print("NAO foi possivel obter config do Blocks.")
    sys.exit(2)

comps = {c["id"]: c for c in cfg["components"]}
errors = []


def walk(node, ancestors=()):
    yield node, ancestors
    for ch in node.get("children", []) or []:
        yield from walk(ch, ancestors + (node,))


def ctype(node):
    return comps.get(node["id"], {}).get("type")


def props(node):
    return comps.get(node["id"], {}).get("props", {}) or {}


tab_parents = {}
for node, anc in walk(cfg["layout"]):
    t = ctype(node)
    if t == "tabitem":
        parent = anc[-1] if anc else None
        if not parent or ctype(parent) != "tabs":
            errors.append(f"Tab '{props(node).get('label')}' nao esta dentro de gr.Tabs()")
        tab_parents.setdefault(props(node).get("label"), set()).add(parent["id"] if parent else None)
    if t == "tabs":
        labels = [props(c).get("label") for c in (node.get("children") or []) if ctype(c) == "tabitem"]
        if len(labels) != len(set(labels)):
            errors.append(f"Tabs com rotulos duplicados: {labels}")
    if t == "group":
        # grupos de modo: visibilidade inicial
        pass

for rotulo in ("Galeria", "Arquivo local", "Baixar do YouTube"):
    if rotulo not in tab_parents:
        errors.append(f"Aba '{rotulo}' nao encontrada")

same = (tab_parents.get("Galeria") == tab_parents.get("Arquivo local") == tab_parents.get("Baixar do YouTube"))
if not same:
    errors.append("Galeria nao compartilha o mesmo gr.Tabs de 'Arquivo local'/'Baixar do YouTube'")

if errors:
    print("FALHOU:")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print("OK: arvore de abas correta.")
