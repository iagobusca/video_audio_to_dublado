"""M1 - ingestao: normaliza entrada (arquivo ou URL) para wav 16k."""
import subprocess
from pathlib import Path


def run(entrada, workdir):
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    out = workdir / "input.wav"
    # yt-dlp se URL
    if str(entrada).startswith("http"):
        subprocess.run(["yt-dlp", "-x", "--audio-format", "wav", "-o", str(workdir / "input.%(ext)s"), str(entrada)], check=False)
    # ffmpeg normalize
    src = entrada
    if str(entrada).startswith("http"):
        src = workdir / "input.wav"
    subprocess.run(["ffmpeg", "-y", "-i", str(src), "-ar", "16000", "-ac", "1", str(out)], check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out
