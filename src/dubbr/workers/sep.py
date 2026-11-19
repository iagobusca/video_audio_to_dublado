"""Worker separacao (Demucs htdemucs_ft) - real."""
import argparse
import subprocess
import sys
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI()


class Req(BaseModel):
    audio_path: str
    workdir: str


@app.get("/health")
def health():
    return {"ok": True, "worker": "sep"}


@app.post("/separate")
def separate(req: Req):
    out = Path(req.workdir) / "sep"
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "-m", "demucs.separate", "--two-stems=vocals",
                    "-n", "htdemucs_ft", "-o", str(out), req.audio_path], check=True)
    d = out / "htdemucs_ft" / Path(req.audio_path).stem
    return {"vocal": str(d / "vocals.wav"), "instrumental": str(d / "no_vocals.wav")}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8012)
    a = ap.parse_args()
    uvicorn.run(app, host="127.0.0.1", port=a.port, log_level="warning")
