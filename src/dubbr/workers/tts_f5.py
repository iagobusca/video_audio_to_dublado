"""Worker TTS F5-pt-br - experimental. Retorna 501."""
import argparse
from fastapi import FastAPI, HTTPException
import uvicorn

app = FastAPI()


@app.get("/health")
def health():
    return {"ok": False, "worker": "tts-f5", "status": "experimental"}


@app.post("/tts")
def tts():
    raise HTTPException(status_code=501, detail="F5-pt-br experimental (instale f5-tts no venv_workers)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8023)
    a = ap.parse_args()
    uvicorn.run(app, host="127.0.0.1", port=a.port, log_level="warning")
