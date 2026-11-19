"""Worker TTS Qwen3 - experimental (requer qwentts.cpp build Windows). Retorna 501."""
import argparse
from fastapi import FastAPI, HTTPException, Response
import uvicorn

app = FastAPI()


@app.get("/health")
def health():
    return {"ok": False, "worker": "tts-qwen", "status": "experimental"}


@app.post("/tts")
def tts():
    raise HTTPException(status_code=501, detail="Qwen3-TTS requer qwentts.cpp (experimental, build Windows nao validado)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8021)
    a = ap.parse_args()
    uvicorn.run(app, host="127.0.0.1", port=a.port, log_level="warning")
