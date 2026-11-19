"""Aba Config: VRAM, caminhos, glossario (ESPEC 4)."""
import gradio as gr
from ..config import VRAM_BUDGET_GB, MODELS_DIR, OUTPUT_DIR


def build(jm):
    with gr.Tab("Config"):
        vram = gr.Slider(1.0, 16.0, value=VRAM_BUDGET_GB, label="Orcamento VRAM (GB)")
        models_path = gr.Textbox(value=str(MODELS_DIR), label="Pasta modelos")
        out_path = gr.Textbox(value=str(OUTPUT_DIR), label="Pasta saidas")
        gloss = gr.Textbox(label="Glossario (yaml)", lines=10, value="")
        gr.Markdown("Idioma de saida fixo: pt-BR (v1.1)")
    return
