"""Worker TTS Chatterbox Multilingual V3 pt-BR - real (clone via audio_prompt_path)."""
import argparse
import io
import os
import re
from pathlib import Path
import numpy as np
import soundfile as sf
import torch
from fastapi import FastAPI, Response
from pydantic import BaseModel
import uvicorn

app = FastAPI()
MODEL = None
SR = 24000
PACK = Path(os.environ.get("CHATTERBOX_PACK", ""))


def _chunks(text, limit=300):
    parts = re.split(r"(?<=[.!?;])\s+", text.strip())
    out, cur = [], ""
    for p in parts:
        if len(cur) + len(p) + 1 <= limit:
            cur = (cur + " " + p).strip()
        else:
            if cur:
                out.append(cur)
            while len(p) > limit:
                out.append(p[:limit])
                p = p[limit:]
            cur = p
    if cur:
        out.append(cur)
    return out or [""]


@app.on_event("startup")
def load():
    global MODEL, SR
    try:
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS as TTS
    except ImportError:
        from chatterbox.tts import ChatterboxTTS as TTS
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    MODEL = TTS.from_pretrained(dev)
    if PACK and (PACK / "t3_pt_br.safetensors").exists():
        from safetensors.torch import load_file
        MODEL.t3.load_state_dict(load_file(str(PACK / "t3_pt_br.safetensors")), strict=False)
        s3 = PACK / "s3gen_v3.safetensors"
        if s3.exists():
            MODEL.s3gen.load_state_dict(load_file(str(s3)), strict=False)
    SR = int(MODEL.sr)


class Req(BaseModel):
    text: str
    ref_wav: str | None = None
    ref_text: str | None = None
    language_id: str = "pt"
    exaggeration: float = 0.5
    temperature: float = 0.8
    cfg_weight: float = 0.5


@app.get("/health")
def health():
    return {"ok": MODEL is not None, "worker": "tts-chatterbox", "sr": SR}


@app.post("/tts")
def tts(req: Req):
    kw = {"language_id": req.language_id, "exaggeration": req.exaggeration,
          "temperature": req.temperature, "cfg_weight": req.cfg_weight}
    if req.ref_wav:
        kw["audio_prompt_path"] = req.ref_wav
    pieces = []
    for chunk in _chunks(req.text):
        wav = MODEL.generate(chunk, **kw)
        pieces.append(wav.squeeze(0).cpu().numpy().astype("float32"))
    arr = np.concatenate(pieces) if pieces else np.zeros(1, dtype="float32")
    buf = io.BytesIO()
    sf.write(buf, arr, SR, format="WAV", subtype="PCM_16")
    return Response(content=buf.getvalue(), media_type="audio/wav")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8022)
    ap.add_argument("--pack", default="")
    a = ap.parse_args()
    if a.pack:
        os.environ["CHATTERBOX_PACK"] = a.pack
    uvicorn.run(app, host="127.0.0.1", port=a.port, log_level="warning")
