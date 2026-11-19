"""Aba Trabalho: modos A/B/C (ESPEC 4)."""
import gradio as gr
import sys, numpy as np, soundfile as sf
from pathlib import Path
import uuid

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from dubbr.youtube import baixar as yt_baixar, listar_resolucoes
from dubbr.catalog import modelos as cat_modelos, variantes as cat_variantes
from dubbr.models_manager import status as model_status, baixar as model_baixar, model_dir


def _tts_models():
    return [m["id"] for m in cat_modelos() if m.get("papel") == "tts"]


def _downloaded_quants(mid):
    # retorna variantes que existem no disco
    d = model_dir(mid)
    if not d.exists():
        return []
    vs = cat_variantes(mid)
    out = []
    for v in vs:
        # heuristica: se pasta tem arquivos
        if any(d.rglob("*")):
            out.append(v)
    # se nada, retorna todas (permitir baixar)
    return out if out else vs


def _placeholder_audio(out_path):
    sr = 22050
    t = np.linspace(0, 1.0, sr, endpoint=False)
    wav = 0.1 * np.sin(2 * np.pi * 440 * t).astype("float32")
    sf.write(out_path, wav, sr)
    return out_path


def build(jm):
    with gr.Tab("Trabalho"):
        modo = gr.Radio(["A - Clonar voz", "B - Texto->audio", "C - Dublagem"], value="C - Dublagem", label="Modo")

        # ---------- Modo A ----------
        with gr.Group(visible=True) as gA:
            gr.Markdown("### Modo A - Clonar voz + texto")
            with gr.Row():
                ref_audio = gr.Audio(label="Referencia (upload)", type="filepath")
                ref_lib = gr.Dropdown(choices=[], label="Ou escolher da biblioteca de vozes", value=None)
            txt_a = gr.Textbox(label="Texto a sintetizar", lines=4)
            with gr.Row():
                backend_a = gr.Dropdown(choices=_tts_models(), value=_tts_models()[0] if _tts_models() else None, label="Backend TTS")
                quant_a = gr.Dropdown(choices=[], label="Quantizacao")
            intens = gr.Slider(0, 1, value=0.5, label="Intensidade (manual)")
            with gr.Row():
                btn_detect = gr.Button("Detectar da referencia (SER)")
                btn_gen_a = gr.Button("Gerar audio")
            ref_text_a = gr.Textbox(label="ref_text (Qwen3, editavel)", lines=2)
            xvec_a = gr.Checkbox(label="x_vector_only (sem transcricao, qualidade menor)")
            out_a = gr.Audio(label="Saida")
            status_a = gr.Textbox(label="Status", lines=6)

            def on_backend_a(b):
                qs = cat_variantes(b) if b else []
                return gr.update(choices=qs, value=(qs[0] if qs else None))
            backend_a.change(on_backend_a, inputs=backend_a, outputs=quant_a)

            def detect_ser(ref):
                if not ref:
                    return 0.5, "Informe uma referencia."
                return 0.7, "SER executado (stub): arousal=0.7"

            btn_detect.click(detect_ser, inputs=ref_audio, outputs=[intens, status_a])

            def gen_a(ref, text, backend, quant, intensity, ref_text, xvec):
                if not text or not text.strip():
                    return None, "Informe o texto."
                sid = uuid.uuid4().hex[:6]
                out_path = ROOT / "saidas" / f"modoA_{sid}.wav"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                _placeholder_audio(out_path)
                msgs = [f"Backend: {backend} ({quant})", f"Intensidade: {intensity}", f"ref_text: {ref_text}", f"x_vector_only: {xvec}", "Audio gerado (placeholder - backend TTS a integrar)."]
                return str(out_path), "\n".join(msgs)

            btn_gen_a.click(gen_a, inputs=[ref_audio, txt_a, backend_a, quant_a, intens, ref_text_a, xvec_a],
                           outputs=[out_a, status_a])

        # ---------- Modo B ----------
        with gr.Group(visible=True) as gB:
            gr.Markdown("### Modo B - Texto->audio (sem clone)")
            gr.Markdown("Aviso: presets do CustomVoice nao tem falante nativo de pt; VoiceDesign e o caminho para voz BR.")
            txt_b = gr.Textbox(label="Texto", lines=4)
            modo_b = gr.Radio(["CustomVoice (presets)", "VoiceDesign (descricao)", "Chatterbox pt-br"], value="VoiceDesign (descricao)", label="Variante")
            with gr.Group():
                preset_voice = gr.Dropdown(choices=["Vivian", "Serena", "Uncle_Fu", "Dylan", "Eric", "Ryan", "Aiden", "Ono_Anna", "Sohee"],
                                          value="Ryan", label="Preset (CustomVoice)")
                instruct_b = gr.Textbox(label="Instruct (emoção/estilo)", value="fale com entusiasmo")
                voice_desc = gr.Textbox(label="Descreva a voz (VoiceDesign)", value="voz masculina brasileira, 40 anos, locutor de documentario, ritmo calmo")
                exaggeration_b = gr.Slider(0, 1, value=0.5, label="Exaggeration (Chatterbox)")
            btn_gen_b = gr.Button("Gerar audio")
            out_b = gr.Audio(label="Saida")
            status_b = gr.Textbox(label="Status", lines=6)

            def gen_b(text, modo, pv, instr, desc, exag):
                if not text or not text.strip():
                    return None, "Informe o texto."
                sid = uuid.uuid4().hex[:6]
                out_path = ROOT / "saidas" / f"modoB_{sid}.wav"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                _placeholder_audio(out_path)
                msgs = [f"Modo: {modo}", f"Texto: {text[:60]}", "Audio gerado (placeholder - backend TTS a integrar)."]
                return str(out_path), "\n".join(msgs)

            btn_gen_b.click(gen_b, inputs=[txt_b, modo_b, preset_voice, instruct_b, voice_desc, exaggeration_b],
                           outputs=[out_b, status_b])

        # ---------- Modo C ----------
        with gr.Group(visible=True) as gC:
            gr.Markdown("### Modo C - Dublagem")
            with gr.Tabs():
                with gr.Tab("Arquivo local"):
                    inp_file = gr.File(label="Arraste e solte ou clique para selecionar audio/video",
                                       file_types=[".mp4", ".mkv", ".mov", ".webm", ".wav", ".mp3", ".flac", ".m4a"])
                with gr.Tab("Baixar do YouTube"):
                    inp_url = gr.Textbox(label="URL do YouTube", placeholder="https://www.youtube.com/watch?v=...")
                    btn_list = gr.Button("1) Listar resolucoes")
                    sel_res = gr.Dropdown(choices=[], label="Resolucao (selecione)", value=None)
                    btn_dl = gr.Button("2) Baixar video")
                    dl_status = gr.Textbox(label="Status download", lines=16)

                    def do_list(url):
                        if not url or not url.strip():
                            return gr.update(choices=[], value=None), "Informe a URL."
                        ress = listar_resolucoes(url.strip())
                        choices = [str(r) for r in ress]
                        return gr.update(choices=choices, value=(choices[0] if choices else None)), f"Resolucoes encontradas: {choices}"

                    def do_download(url, res):
                        if not url or not url.strip():
                            yield "Informe a URL do YouTube."
                            return
                        msgs = []

                        def cb(m):
                            msgs.append(m)

                        r = yt_baixar(url.strip(), resolucao=res, progress_cb=cb)
                        out = "\n".join(msgs)
                        if r:
                            out += f"\n\nARQUIVO BAIXADO:\n{r}"
                        else:
                            out += "\n\nFALHA no download."
                        yield out

                    btn_list.click(do_list, inputs=inp_url, outputs=[sel_res, dl_status])
                    btn_dl.click(do_download, inputs=[inp_url, sel_res], outputs=dl_status)

            preset = gr.Dropdown(["leve", "equilibrado", "maximo", "custom"], value="equilibrado", label="Preset")
            revisar = gr.Checkbox(label="Pausar para revisar traducao")
            btn = gr.Button("Iniciar pipeline")
            progress = gr.Textbox(label="Progresso", lines=12)
            out_video = gr.Video(label="Resultado (video)")
            out_audio = gr.Audio(label="Resultado (audio)")
            btn.click(lambda *a: "pipeline stub ok", inputs=[inp_file, inp_url, preset, revisar], outputs=progress)

        # ---------- Galeria ----------
        with gr.Tab("Galeria"):
            gr.Markdown("### Galeria de midias")
            with gr.Tabs():
                with gr.Tab("Audio"):
                    gal_audio = gr.Dataframe(headers=["nome", "caminho", "status"], value=[], interactive=False)
                    btn_refresh_audio = gr.Button("Atualizar lista de audios")
                with gr.Tab("Video"):
                    gal_video = gr.Dataframe(headers=["nome", "caminho", "status"], value=[], interactive=False)
                    btn_refresh_video = gr.Button("Atualizar lista de videos")
                    sel_video = gr.Textbox(label="Caminho do video selecionado (cole da tabela)", visible=True)
                    btn_dublar = gr.Button("Dublar video selecionado")
                    pipeline_panel = gr.HTML(label="Pipeline", value="<div style='padding:10px;border:1px solid #ccc'>Selecione um video e clique em Dublar.</div>")
                    btn_start = gr.Button("Start Dublagem")
                    out_gal_video = gr.Video(label="Resultado (video dublado)")

            import os
            VIDEO_EXT = (".mp4", ".mkv", ".mov", ".webm")
            AUDIO_EXT = (".wav", ".mp3", ".flac", ".m4a")

            def list_media(exts, roots):
                rows = []
                for root in roots:
                    if not root.exists():
                        continue
                    for p in root.rglob("*"):
                        if p.is_file() and p.suffix.lower() in exts:
                            # status dublado?
                            status = "original"
                            dub = p.parent / "dublado.mp4" if p.suffix.lower() in VIDEO_EXT else p.parent / "dublado.wav"
                            if dub.exists():
                                status = "dublado disponivel"
                            rows.append([p.name, str(p), status])
                return rows

            def refresh_audio():
                return list_media(AUDIO_EXT, [ROOT / "saidas", ROOT / "youtube_download", ROOT / "vozes"])

            def refresh_video():
                return list_media(VIDEO_EXT, [ROOT / "youtube_download", ROOT / "saidas"])

            btn_refresh_audio.click(refresh_audio, outputs=gal_audio)
            btn_refresh_video.click(refresh_video, outputs=gal_video)

            def on_select_video(evt: gr.SelectData):
                # evt.index -> (row, col)
                try:
                    row = evt.index[0]
                    # nao temos acesso direto; retornar placeholder
                except Exception:
                    pass
                return ""

            def dublar_selected(path):
                if not path:
                    return "<div>Selecione um video na tabela.</div>"
                html = f"""
                <div style='padding:12px;border:1px solid #888;border-radius:8px'>
                  <h3>Pipeline de Dublagem</h3>
                  <p><b>Video:</b> {path}</p>
                  <p><b>Preset:</b> equilibrado (leve/equilibrado/maximo/custom)</p>
                  <p><b>Estagios:</b> M1 ingestao | M2 separacao | M3 ASR | M4 SER | M5 traducao | M6 TTS | M7 mux</p>
                  <p><b>Status:</b> aguardando Start Dublagem</p>
                </div>
                """
                return html

            btn_dublar.click(dublar_selected, inputs=sel_video, outputs=pipeline_panel)
            btn_start.click(lambda: "Dublagem iniciada (stub).", outputs=progress)

        # visibilidade por modo
        def on_modo(m):
            show_a = (m == "A - Clonar voz")
            show_b = (m == "B - Texto->audio")
            show_c = (m == "C - Dublagem")
            return (gr.update(visible=show_a), gr.update(visible=show_b), gr.update(visible=show_c))
        modo.change(on_modo, inputs=modo, outputs=[gA, gB, gC])
        # estado inicial
        gA.visible = False
        gB.visible = False
        gC.visible = True
    return
