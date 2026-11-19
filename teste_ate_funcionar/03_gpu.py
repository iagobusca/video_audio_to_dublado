"""Verifica GPU/CUDA disponivel para cada backend."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.stdout.reconfigure(encoding="utf-8")
import torch
print("torch", torch.__version__)
print("cuda available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("device:", torch.cuda.get_device_name(0))
    print("vram GB:", round(torch.cuda.get_device_properties(0).total_memory/1e9,2))
try:
    import ctranslate2
    print("ctranslate2 cuda devices:", ctranslate2.get_cuda_device_count())
except Exception as e:
    print("ctranslate2 err:", e)
import subprocess
from pathlib import Path as P
llama = ROOT / "bin" / "llama.cpp" / "llama-server.exe"
print("llama-server exists:", llama.exists())
