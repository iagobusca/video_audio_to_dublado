"""Gerenciador de modelos: download/apagar do disco (ESPEC 3)."""
import shutil
from pathlib import Path
from .config import MODELS_DIR, HF_HOME
from .catalog import modelos, por_id, variantes as cat_variantes

try:
    from huggingface_hub import hf_hub_download, snapshot_download, scan_cache_dir
    HF_OK = True
except Exception:
    HF_OK = False


def model_dir(mid):
    return MODELS_DIR / mid


def status(mid, variante=None):
    d = model_dir(mid)
    if not d.exists():
        return "nao_baixado"
    # heuristica: se pasta nao vazia -> pronto
    if any(d.iterdir()):
        return "pronto"
    return "nao_baixado"


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


def tamanho_disco(mid, variante=None):
    d = model_dir(mid)
    if not d.exists():
        return 0
    total = 0
    for p in d.rglob("*"):
        if p.is_file():
            total += p.stat().st_size
    if total == 0:
        return tamanho_esperado(mid, variante)
    return total


def baixar(mid, variante=None, progress_cb=None):
    m = por_id(mid)
    if m is None:
        raise ValueError(f"modelo {mid} nao encontrado")
    repo = m["repo"]
    dest = model_dir(mid)
    dest.mkdir(parents=True, exist_ok=True)
    if "arquivos" in m:
        # GGUF: baixa arquivo a arquivo
        arqs = m["arquivos"].get(variante, []) if variante else []
        if not arqs and m["arquivos"]:
            variante = next(iter(m["arquivos"]))
            arqs = m["arquivos"][variante]
        for a in arqs:
            if progress_cb:
                progress_cb(f"baixando {a}")
            hf_hub_download(repo_id=repo, filename=a, local_dir=str(dest), local_dir_use_symlinks=False)
        # limpeza leve de metadados
        for md in dest.rglob("*.metadata"):
            try: md.unlink()
            except Exception: pass
    else:
        # torch repo: snapshot_download sem symlinks, apenas pesos/configs uteis
        allow = ["*.safetensors", "*.bin", "*.pt", "*.gguf", "*.json", "*.txt", "*.yaml", "*.yml",
                 "*.model", "*.vocab", "README.md", "*.py", "*.cfg", "mmproj*"]
        ignore = ["*.pt"]  # preferir safetensors/bin; .pt removido se safetensors existir
        # se nao houver safetensors, manter .pt
        try:
            snapshot_download(repo_id=repo, local_dir=str(dest), local_dir_use_symlinks=False,
                             allow_patterns=allow, ignore_patterns=ignore)
        except Exception:
            snapshot_download(repo_id=repo, local_dir=str(dest), local_dir_use_symlinks=False,
                             allow_patterns=allow)
        for md in dest.rglob("*.metadata"):
            try: md.unlink()
            except Exception: pass
        cache = dest / ".cache"
        if cache.exists():
            shutil.rmtree(cache, ignore_errors=True)
    return dest


def limpar_extras(mid):
    """Remove checkpoints duplicados e cache HF local, mantendo pesos principais."""
    d = model_dir(mid)
    if not d.exists():
        return False
    # remove .cache
    cache = d / ".cache"
    if cache.exists():
        shutil.rmtree(cache)
    # se houver safetensors, remove .pt duplicados
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
