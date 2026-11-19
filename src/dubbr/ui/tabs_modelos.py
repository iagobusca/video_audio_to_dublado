"""Aba Modelos: separada por funcao (Extrair texto / Traducao / Audio-texto dublado)."""
import gradio as gr
from ..catalog import modelos as cat_modelos_list, variantes as cat_variantes
from ..models_manager import status, tamanho_esperado, baixar, apagar, limpar_extras, model_dir


def _modelos_por_papel(papeis):
    return [m for m in cat_modelos_list() if m.get("papel") in papeis]


def _rows(papeis):
    rows = []
    for m in _modelos_por_papel(papeis):
        mid = m["id"]
        d = model_dir(mid)
        real_sz = 0
        if d.exists():
            real_sz = sum(p.stat().st_size for p in d.rglob("*") if p.is_file())
        if real_sz:
            sz_txt = f"{real_sz/1e9:.2f} GB (disco)"
        else:
            esp = tamanho_esperado(mid)
            sz_txt = f"~{esp/1e9:.2f} GB (esperado)" if esp else "-"
        rows.append([mid, m.get("papel"), m.get("repo", "-"), ", ".join(cat_variantes(mid)), sz_txt, status(mid)])
    return rows


def _subtab(papeis, jm):
    with gr.Column():
        table = gr.Dataframe(headers=["id", "papel", "repo", "quantizacoes", "tamanho", "status"],
                            value=_rows(papeis), interactive=False)
        choices = [m["id"] for m in _modelos_por_papel(papeis)]
        with gr.Row():
            sel_modelo = gr.Dropdown(choices=choices, label="Modelo", value=None)
            sel_quant = gr.Dropdown(choices=[], label="Quantizacao", value=None)

        def on_model_change(mid):
            vs = cat_variantes(mid) if mid else []
            return gr.update(choices=vs, value=(vs[0] if vs else None))

        sel_modelo.change(on_model_change, inputs=sel_modelo, outputs=sel_quant)

        with gr.Row():
            btn_dl = gr.Button("Baixar")
            btn_rm = gr.Button("Apagar")
            btn_clean = gr.Button("Limpar extras")
            btn_refresh = gr.Button("Atualizar tabela")
        log = gr.Textbox(label="Log", lines=8)

        def do_dl(mid, v):
            if not mid:
                return "Selecione um modelo."
            try:
                baixar(mid, v)
                return f"OK: {mid} ({v}) baixado"
            except Exception as e:
                return f"ERRO: {e}"

        def do_rm(mid):
            if not mid:
                return "Selecione um modelo."
            try:
                apagar(mid, em_uso=False)
                return f"OK: {mid} apagado"
            except Exception as e:
                return f"ERRO: {e}"

        def do_clean(mid):
            if not mid:
                return "Selecione um modelo."
            try:
                limpar_extras(mid)
                return f"OK: extras de {mid} removidos"
            except Exception as e:
                return f"ERRO: {e}"

        def do_refresh():
            return _rows(papeis)

        btn_dl.click(do_dl, inputs=[sel_modelo, sel_quant], outputs=log)
        btn_rm.click(do_rm, inputs=[sel_modelo], outputs=log)
        btn_clean.click(do_clean, inputs=[sel_modelo], outputs=log)
        btn_refresh.click(do_refresh, outputs=table)


def build(jm):
    with gr.Tab("Modelos"):
        gr.Markdown("### Gerenciador de modelos (por funcao)")
        with gr.Tabs():
            with gr.Tab("Extrair texto"):
                _subtab(["asr"], jm)
            with gr.Tab("Traducao"):
                _subtab(["traducao"], jm)
            with gr.Tab("Audio/Texto dublado"):
                _subtab(["tts", "ser", "separacao"], jm)
    return
