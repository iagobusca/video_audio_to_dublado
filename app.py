"""app.py - entrada principal (Gradio UI, ESPEC v1.1)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import gradio as gr
from dubbr.config import ensure_dirs, HOST, PORT
from dubbr.job_manager import JobManager
from dubbr.ui.tabs_trabalho import build as build_trabalho
from dubbr.ui.tabs_modelos import build as build_modelos
from dubbr.ui.tabs_jobs import build as build_jobs
from dubbr.ui.tabs_config import build as build_config

ensure_dirs()
jm = JobManager()

with gr.Blocks(title="dubbr - Dublagem automatica EN->PT-BR") as demo:
    gr.Markdown("# dubbr v1.1 - Dublagem automatica EN->PT-BR")
    build_trabalho(jm)
    build_modelos(jm)
    build_jobs(jm)
    build_config(jm)

if __name__ == "__main__":
    demo.launch(server_name=HOST, server_port=PORT, inbrowser=True)
