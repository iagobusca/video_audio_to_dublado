"""Baixa llama-server.exe (llama.cpp) para bin/llama.cpp/. Experimental: parakeet.cpp/qwentts.cpp."""
import os
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "bin" / "llama.cpp"
DEST.mkdir(parents=True, exist_ok=True)
URL = os.environ.get("LLAMA_URL", "https://github.com/ggerganov/llama.cpp/releases/latest/download/llama-bin-win-cuda-x64.zip")


def main():
    if (DEST / "llama-server.exe").exists():
        print("llama-server.exe ja presente.")
        return 0
    zip_path = DEST / "llama.zip"
    print(f"Baixando {URL} ...")
    urllib.request.urlretrieve(URL, zip_path)
    print("Extraindo...")
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(DEST)
    zip_path.unlink(missing_ok=True)
    # move executavel se estiver em subpasta
    for p in DEST.rglob("llama-server.exe"):
        if p != DEST / "llama-server.exe":
            p.replace(DEST / "llama-server.exe")
    print("OK:", DEST / "llama-server.exe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
