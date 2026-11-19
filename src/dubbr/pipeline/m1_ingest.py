"""M1 - ingestao robusta: wav 16k para ASR + preserva video original para o mux."""
import subprocess
import sys
from pathlib import Path

VIDEO_EXT = (".mp4", ".mkv", ".mov", ".webm")


def run(entrada, workdir):
    wd = Path(workdir)
    wd.mkdir(parents=True, exist_ok=True)
    out = wd / "input.wav"
    src = Path(str(entrada))
    video = None
    if str(entrada).startswith(("http://", "https://")):
        subprocess.run([sys.executable, "-m", "yt_dlp",
                        "-f", "bestvideo+bestaudio/best", "--merge-output-format", "mp4",
                        "-o", str(wd / "original.%(ext)s"), str(entrada)], check=True)
        cands = list(wd.glob("original.*"))
        if not cands:
            raise RuntimeError("yt-dlp nao gerou arquivo de saida")
        src = cands[0]
    elif not src.exists():
        raise FileNotFoundError(f"Entrada nao encontrada: {src}")
    if src.suffix.lower() in VIDEO_EXT:
        video = str(src)
    subprocess.run(["ffmpeg", "-y", "-i", str(src), "-ar", "16000", "-ac", "1", str(out)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not out.exists() or out.stat().st_size == 0:
        raise RuntimeError("ffmpeg falhou na normalizacao para wav 16k")
    return {"audio": str(out), "video": video, "source": str(src)}
