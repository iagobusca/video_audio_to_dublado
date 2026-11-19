"""Instala torch CUDA (cu121) no runtime embutido."""
import subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
py = ROOT / "bin" / "runtime" / "python" / "python.exe"
if not py.exists():
    py = Path(sys.executable)
print("Usando python:", py)
subprocess.check_call([str(py), "-m", "pip", "install", "--upgrade", "torch", "torchaudio",
                      "--index-url", "https://download.pytorch.org/whl/cu121"])
print("OK")
