"""Catalogo de modelos (leitura do catalogo.yaml)."""
from .config import load_catalogo


def modelos():
    return load_catalogo().get("modelos", [])


def por_papel(papel):
    return [m for m in modelos() if m.get("papel") == papel]


def por_id(mid):
    for m in modelos():
        if m["id"] == mid:
            return m
    return None


def variantes(mid):
    m = por_id(mid)
    if not m:
        return []
    if "arquivos" in m:
        return list(m["arquivos"].keys())
    return m.get("variantes", [])


def binarios():
    return load_catalogo().get("binarios", [])
