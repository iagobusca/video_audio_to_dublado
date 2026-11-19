"""M3 - ASR real: faster-whisper (CUDA/CPU), modelo local primeiro."""
from pathlib import Path
from ..config import MODELS_DIR, HF_HOME


def run(audio_path, workdir, preset="equilibrado"):
    import ctranslate2
    from faster_whisper import WhisperModel
    size = {"leve": "small", "equilibrado": "large-v3", "maximo": "large-v3"}.get(preset, "large-v3")
    compute = {"leve": "int8", "equilibrado": "float16", "maximo": "float16"}.get(preset, "float16")
    device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
    if device == "cpu" and compute == "float16":
        compute = "int8"
    local = MODELS_DIR / f"faster-whisper-{size}"
    model = WhisperModel(str(local) if local.exists() else size,
                         device=device, compute_type=compute, download_root=str(HF_HOME))
    try:
        segs, _info = model.transcribe(str(audio_path), language="en", vad_filter=True)
        out = [{"start": float(s.start), "end": float(s.end),
                "text": s.text.strip(), "speaker": "S1"}
               for s in segs if s.text.strip()]
    finally:
        del model
    if not out:
        raise RuntimeError("ASR nao retornou segmentos (audio sem fala?)")
    return out
