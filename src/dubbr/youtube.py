"""Download de videos do YouTube com selecao de resolucao e progresso (yt-dlp)."""
from pathlib import Path
from .config import ROOT

YTDOWN_DIR = ROOT / "youtube_download"


def ensure_dir():
    YTDOWN_DIR.mkdir(parents=True, exist_ok=True)
    return YTDOWN_DIR


def listar_resolucoes(url):
    """Retorna lista de resolucoes de video disponiveis (strings ex: '720', '1080')."""
    try:
        import yt_dlp
    except Exception:
        return []
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception:
        return []
    ress = set()
    for f in info.get("formats", []):
        if f.get("vcodec") and f.get("vcodec") != "none":
            h = f.get("height")
            if h:
                ress.add(int(h))
    # incluir best
    if not ress:
        return ["best"]
    return sorted(ress, reverse=True)


def baixar(url, resolucao=None, progress_cb=None):
    ensure_dir()
    if progress_cb:
        progress_cb("1/5 Preparando download...")
    try:
        import yt_dlp
    except Exception as e:
        if progress_cb:
            progress_cb(f"yt-dlp nao instalado: {e}")
        return None

    outtmpl = str(YTDOWN_DIR / "%(title)s [%(id)s].%(ext)s")

    def hook(d):
        if progress_cb is None:
            return
        status = d.get("status")
        if status == "downloading":
            pct = d.get("_percent_str", "").strip()
            speed = d.get("_speed_str", "").strip()
            eta = d.get("_eta_str", "").strip()
            fname = d.get("filename", "")
            progress_cb(f"Baixando: {pct} | {speed} | ETA {eta} | {Path(fname).name}")
        elif status == "finished":
            progress_cb(f"Download concluido: {Path(d.get('filename','')).name}")

    # montar formato
    if resolucao and resolucao != "best":
        fmt = f"bestvideo[height<={resolucao}]+bestaudio/best[height<={resolucao}]/best"
    else:
        fmt = "bestvideo+bestaudio/best"

    ydl_opts = {
        "outtmpl": outtmpl,
        "format": fmt,
        "merge_output_format": "mp4",
        "progress_hooks": [hook],
        "quiet": True,
        "no_warnings": True,
    }

    if progress_cb:
        progress_cb("2/5 Listando formatos/resolucoes...")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if progress_cb:
                progress_cb(f"3/5 Baixando em {resolucao}p..." if resolucao and resolucao != "best" else "3/5 Baixando melhor qualidade...")
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            p = Path(filename)
            if not p.exists():
                p = p.with_suffix(".mp4")
            if progress_cb:
                progress_cb(f"4/5 Finalizando... arquivo: {p.name}")
            return str(p)
    except Exception as e:
        if progress_cb:
            progress_cb(f"ERRO: {e}")
        return None
