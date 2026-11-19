"""Worker SER (audeering wav2vec2 dim) - real. Modelo local primeiro, senao HF_HOME."""
import argparse
import os
from pathlib import Path
import numpy as np
import soundfile as sf
import torch
import torchaudio
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from transformers import AutoModelForAudioClassification, AutoFeatureExtractor

MODEL_ID = "audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim"
LOCAL = Path(os.environ.get("SER_MODEL_DIR", ""))
app = FastAPI()
model = None
fe = None


@app.on_event("startup")
def load():
    global model, fe
    src = str(LOCAL) if LOCAL.exists() else MODEL_ID
    fe = AutoFeatureExtractor.from_pretrained(src)
    model = AutoModelForAudioClassification.from_pretrained(src)
    model.eval()
    if torch.cuda.is_available():
        model = model.cuda()


class Req(BaseModel):
    audio_path: str


@app.get("/health")
def health():
    return {"ok": model is not None, "worker": "ser"}


@app.post("/ser")
def ser(req: Req):
    wav, sr = sf.read(req.audio_path, dtype="float32")
    if wav.ndim > 1:
        wav = wav.mean(axis=1)
    if sr != 16000:
        wav = torchaudio.functional.resample(torch.from_numpy(wav), sr, 16000).numpy()
    inputs = fe(wav, sampling_rate=16000, return_tensors="pt", padding=True)
    if torch.cuda.is_available():
        inputs = {k: v.cuda() for k, v in inputs.items()}
    with torch.no_grad():
        logits = model(**inputs).logits[0].cpu().numpy()
    labels = [model.config.id2label[i].lower() for i in range(len(logits))]
    return dict(zip(labels, map(float, logits)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8011)
    ap.add_argument("--model-dir", default="")
    a = ap.parse_args()
    if a.model_dir:
        os.environ["SER_MODEL_DIR"] = a.model_dir
    uvicorn.run(app, host="127.0.0.1", port=a.port, log_level="warning")
