"""Gerenciador de modelos: download/apagar do disco (ESPEC 3 + correcao backend)."""
import shutil
from pathlib import Path
from .config import MODELS_DIR, HF_HOME
from .catalog import modelos, por_id


def model_dir(mid):
    return MODELS_DIR / mid


def status(mid, variante=None):
    m = por_id(mid)
    d = model_dir(mid)
    if not d.exists():
        return "nao_baixado"
    if m and "arquivos" in m:
        vs = [variante] if variante else list(m["arquivos"].keys())
        ok = any(all((d / a).exists() and (d / a).stat().st_size > 0 for a in m["arquivos"][v])
                 for v in vs if v in m["arquivos"])
        return "pronto" if ok else "parcial"
    pesos = list(d.rglob("*.safetensors")) + list(d.rglob("*.bin")) + list(d.rglob("*.gguf"))
    if pesos:
        return "pronto"
    return "parcial" if any(d.iterdir()) else "nao_baixado"


def tamanho_disco(mid, variante=None):
    d = model_dir(mid)
    if not d.exists():
        return 0
    total = 0
    for p in d.rglob("*"):
        if p.is_file():
            total += p.stat().st_size
    if total == 0:
        m = por_id(mid)
        tg = (m or {}).get("tamanhos_gb", {}) or {}
        if variante and variante in tg:
            return int(tg[variante] * 1e9)
        if tg:
            return int(min(tg.values()) * 1e9)
    return total


def tamanho_esperado(mid, variante=None):
    m = por_id(mid)
    if not m:
        return 0
    tg = m.get("tamanhos_gb", {}) or {}
    if variante and variante in tg:
        return int(tg[variante] * 1e9)
    if tg:
        return int(min(tg.values()) * 1e9)
    return 0


def baixar(mid, variante=None, progress_cb=None):
    from huggingface_hub import hf_hub_download, snapshot_download
    m = por_id(mid)
    if m is None:
        raise ValueError(f"modelo {mid} nao encontrado")
    for dep in m.get("deps", []):
        if status(dep) != "pronto":
            if progress_cb:
                progress_cb(f"baixando dependencia {dep}")
            baixar(dep, progress_cb=progress_cb)
    dest = model_dir(mid)
    dest.mkdir(parents=True, exist_ok=True)
    if "arquivos" in m:
        arqs = m["arquivos"].get(variante, []) if variante else []
        if not arqs:
            variante = next(iter(m["arquivos"]))
            arqs = m["arquivos"][variante]
        for a in arqs:
            if progress_cb:
                progress_cb(f"baixando {a}")
            hf_hub_download(repo_id=m["repo"], filename=a, local_dir=str(dest))
    else:
        allow = ["*.safetensors", "*.bin", "*.gguf", "*.json", "*.txt", "*.yaml", "*.yml",
                 "*.model", "*.vocab", "README.md", "*.py", "*.cfg", "mmproj*"]
        snapshot_download(repo_id=m["repo"], local_dir=str(dest),
                          allow_patterns=allow, ignore_patterns=["*.pt"])
    # limpeza leve
    for md in dest.rglob("*.metadata"):
        try:
            md.unlink()
        except Exception:
            pass
    cache = dest / ".cache"
    if cache.exists():
        shutil.rmtree(cache, ignore_errors=True)
    return dest


def limpar_extras(mid):
    d = model_dir(mid)
    if not d.exists():
        return False
    cache = d / ".cache"
    if cache.exists():
        shutil.rmtree(cache)
    safes = list(d.rglob("*.safetensors"))
    if safes:
        for pt in d.rglob("*.pt"):
            try:
                pt.unlink()
            except Exception:
                pass
    return True


def apagar(mid, em_uso=False):
    if em_uso:
        raise RuntimeError(f"modelo {mid} em uso por job ativo - bloqueado")
    d = model_dir(mid)
    if d.exists():
        shutil.rmtree(d)
    return True
