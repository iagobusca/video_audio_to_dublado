"""Aba Trabalho: modos A/B/C + Galeria (ESPEC Correcao UI v1.1.1)."""
import sys
import uuid
from pathlib import Path

import gradio as gr
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from dubbr.youtube import baixar as yt_baixar, listar_resolucoes
from dubbr.catalog import modelos as cat_modelos, variantes as cat_variantes

VIDEO_EXT = (".mp4", ".mkv", ".mov", ".webm")
AUDIO_EXT = (".wav", ".mp3", ".flac", ".m4a")


def _tts_models():
    return [m["id"] for m in cat_modelos() if m.get("papel") == "tts"]


def _placeholder_audio(out_path):
    sr = 22050
    t = np.linspace(0, 1.0, sr, endpoint=False)
    wav = 0.1 * np.sin(2 * np.pi * 440 * t).astype("float32")
    sf.write(out_path, wav, sr)
    return out_path


def _list_media(exts, roots):
    rows = []
    for root in roots:
        if not root.exists():
            continue
        for p in sorted(root.rglob("*")):
            if p.is_file() and p.suffix.lower() in exts:
                dub = p.parent / ("dublado.mp4" if p.suffix.lower() in VIDEO_EXT else "dublado.wav")
                status = "dublado disponivel" if dub.exists() else "original"
                rows.append([p.name, str(p), status])
    return rows


def build(jm):
    with gr.Tab("Trabalho"):
        modo = gr.Radio(["A - Clonar voz", "B - Texto->audio", "C - Dublagem"],
                        value="C - Dublagem", label="Modo")

        # ---------- Modo A (inicia oculto) ----------
        with gr.Group(visible=False) as gA:
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
                if str(backend).startswith("qwen3"):
                    return None, "Qwen3-TTS requer qwentts.cpp (experimental). Use chatterbox-ptbr."
                sid = uuid.uuid4().hex[:6]
                out_path = ROOT / "saidas" / f"modoA_{sid}.wav"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                from dubbr.tts_client import synthesize
                synthesize(text, ref_wav=ref, backend=backend, exaggeration=intensity, out_path=str(out_path))
                msgs = [f"Backend: {backend} ({quant})", f"Intensidade: {intensity}", "Audio gerado (clone da referencia)."]
                return str(out_path), "\n".join(msgs)
            btn_gen_a.click(gen_a, inputs=[ref_audio, txt_a, backend_a, quant_a, intens, ref_text_a, xvec_a],
                            outputs=[out_a, status_a])

        # ---------- Modo B (inicia oculto) ----------
        with gr.Group(visible=False) as gB:
            gr.Markdown("### Modo B - Texto->audio (sem clone)")
            gr.Markdown("Aviso: presets do CustomVoice nao tem falante nativo de pt; VoiceDesign e o caminho para voz BR.")
            txt_b = gr.Textbox(label="Texto", lines=4)
            modo_b = gr.Radio(["CustomVoice (presets)", "VoiceDesign (descricao)", "Chatterbox pt-br"],
                              value="VoiceDesign (descricao)", label="Variante")
            with gr.Group():
                preset_voice = gr.Dropdown(choices=["Vivian", "Serena", "Uncle_Fu", "Dylan", "Eric", "Ryan", "Aiden", "Ono_Anna", "Sohee"],
                                           value="Ryan", label="Preset (CustomVoice)")
                instruct_b = gr.Textbox(label="Instruct (emocao/estilo)", value="fale com entusiasmo")
                voice_desc = gr.Textbox(label="Descreva a voz (VoiceDesign)",
                                        value="voz masculina brasileira, 40 anos, locutor de documentario, ritmo calmo")
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
                from dubbr.tts_client import synthesize
                synthesize(text, backend="chatterbox-ptbr", exaggeration=exag, out_path=str(out_path))
                msgs = [f"Modo: {modo}", f"Texto: {text[:60]}", "Audio gerado (TTS real)."]
                return str(out_path), "\n".join(msgs)
            btn_gen_b.click(gen_b, inputs=[txt_b, modo_b, preset_voice, instruct_b, voice_desc, exaggeration_b],
                            outputs=[out_b, status_b])

        # ---------- Modo C ----------
        with gr.Group(visible=True) as gC:
            gr.Markdown("### Modo C - Dublagem")
            with gr.Tabs():
                with gr.Tab("Arquivo local", id="c_local"):
                    inp_file = gr.File(label="Arraste e solte ou clique para selecionar audio/video",
                                       file_types=[".mp4", ".mkv", ".mov", ".webm", ".wav", ".mp3", ".flac", ".m4a"])
                with gr.Tab("Baixar do YouTube", id="c_yt"):
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
                        out += f"\n\nARQUIVO BAIXADO:\n{r}" if r else "\n\nFALHA no download."
                        yield out
                    btn_list.click(do_list, inputs=inp_url, outputs=[sel_res, dl_status])
                    btn_dl.click(do_download, inputs=[inp_url, sel_res], outputs=dl_status)

                with gr.Tab("Galeria", id="c_galeria") as tab_galeria:
                    with gr.Tabs():
                        with gr.Tab("Audio"):
                            gal_audio = gr.Dataframe(headers=["nome", "caminho", "status"], value=None, interactive=False)
                            btn_refresh_audio = gr.Button("Atualizar lista de audios")
                        with gr.Tab("Video"):
                            gal_video = gr.Dataframe(headers=["nome", "caminho", "status"], value=None, interactive=False)
                            btn_refresh_video = gr.Button("Atualizar lista de videos")
                            sel_video = gr.Textbox(label="Video selecionado", interactive=False)
                            btn_dublar = gr.Button("Dublar video selecionado", variant="primary")
                            out_gal_video = gr.Video(label="Resultado (video dublado)", visible=False)
                    audio_rows = gr.State([])
                    video_rows = gr.State([])

            preset = gr.Dropdown(["leve", "equilibrado", "maximo", "custom"], value="equilibrado", label="Preset")
            revisar = gr.Checkbox(label="Pausar para revisar traducao")
            btn = gr.Button("Iniciar pipeline", variant="primary")
            progress = gr.Textbox(label="Progresso", lines=12, interactive=False)
            out_video = gr.Video(label="Resultado (video)", visible=False)
            out_audio = gr.Audio(label="Resultado (audio)", visible=False)

        with gr.Column(visible=False, elem_id="pipeline-modal") as modal:
            with gr.Group(elem_classes=["pipeline-modal-card"]):
                with gr.Row():
                    gr.Markdown("### Pipeline de Dublagem")
                    btn_close_modal = gr.Button("Fechar ✕", elem_id="pipeline-modal-close", scale=0)
                modal_info = gr.HTML()
                with gr.Row():
                    modal_backend = gr.Dropdown(choices=_tts_models(), value=_tts_models()[0] if _tts_models() else None, label="Backend TTS")
                    modal_preset = gr.Dropdown(["leve", "equilibrado", "maximo", "custom"], value="equilibrado", label="Preset")
                modal_revisar = gr.Checkbox(label="Revisar traducao")
                btn_start = gr.Button("Start Dublagem", variant="primary")
                modal_status = gr.Textbox(label="Status do job", lines=8, interactive=False)
                modal_progress = gr.HTML(value="<div class='dubbr-progress'><div class='bar' style='width:0%'></div></div>")

        timer = gr.Timer(1.0)

        def on_modo(m):
            return (gr.update(visible=(m == "A - Clonar voz")),
                    gr.update(visible=(m == "B - Texto->audio")),
                    gr.update(visible=(m == "C - Dublagem")))
        modo.change(on_modo, inputs=modo, outputs=[gA, gB, gC])

        def refresh_audio():
            rows = _list_media(AUDIO_EXT, [ROOT / "saidas", ROOT / "youtube_download", ROOT / "vozes"])
            return rows, rows

        def refresh_video():
            rows = _list_media(VIDEO_EXT, [ROOT / "youtube_download", ROOT / "saidas"])
            return rows, rows

        def refresh_all():
            ra, _ = refresh_audio()
            rv, _ = refresh_video()
            return ra, ra, rv, rv

        btn_refresh_audio.click(refresh_audio, outputs=[gal_audio, audio_rows])
        btn_refresh_video.click(refresh_video, outputs=[gal_video, video_rows])
        tab_galeria.select(refresh_all, outputs=[gal_audio, audio_rows, gal_video, video_rows])

        def on_select_video(rows, evt: gr.SelectData):
            try:
                return rows[evt.index[0]][1]
            except (IndexError, TypeError):
                return ""
        gal_video.select(on_select_video, inputs=[video_rows], outputs=sel_video)

        def open_modal(path, backend_val, preset_val, revisar_val):
            if not path:
                gr.Warning("Selecione um video na tabela da Galeria (clique em uma linha).")
                return gr.update(visible=False), "", backend_val, preset_val, revisar_val
            html = (
                "<div style='padding:4px 0'>"
                f"<p><b>Video:</b> {path}</p>"
                "<p><b>Estagios:</b> M1 ingestao | M2 separacao | M3 ASR | M4 SER | "
                "M5 traducao | M6 TTS | M7 mux</p>"
                "<p><b>Status:</b> aguardando Start Dublagem</p>"
                "</div>"
            )
            return gr.update(visible=True), html, backend_val, preset_val, revisar_val
        btn_dublar.click(open_modal, inputs=[sel_video, modal_backend, preset, revisar],
                         outputs=[modal, modal_info, modal_backend, modal_preset, modal_revisar])
        btn_close_modal.click(lambda: gr.update(visible=False), outputs=modal)

        def start_job(path, backend_val, preset_val, revisar_val):
            if not path:
                return "Nenhum video selecionado."
            j = jm.submit(path, preset=preset_val, modo="dublagem",
                          extras={"revisar": revisar_val, "backend_tts": backend_val})
            return f"Job {j.id} enfileirado (preset={preset_val}, tts={backend_val}).\nAguardando orchestrator."
        btn_start.click(start_job, inputs=[sel_video, modal_backend, modal_preset, modal_revisar], outputs=modal_status)

        def drain():
            evs = jm.bus.drain()
            if not evs:
                return gr.update(), gr.update()
            lines = [f"[{e['estagio']}] {e['status']} {e['pct']:.0f}% - {e['msg']}" for e in evs]
            pct = max(e["pct"] for e in evs)
            bar = f"<div class='dubbr-progress'><div class='bar' style='width:{pct:.0f}%'></div></div>"
            return "\n".join(lines), bar
        timer.tick(drain, outputs=[modal_status, modal_progress])

        def start_pipeline(arquivo, url, preset_val, revisar_val):
            entrada = arquivo or url
            if not entrada:
                return "Informe um arquivo local ou uma URL do YouTube.", gr.update(visible=False), gr.update(visible=False)
            j = jm.submit(entrada, preset=preset_val, extras={"revisar": revisar_val})
            return (f"Job {j.id} enfileirado (preset={preset_val}). Acompanhe o progresso.",
                    gr.update(visible=True), gr.update(visible=True))
        btn.click(start_pipeline, inputs=[inp_file, inp_url, preset, revisar], outputs=[progress, out_video, out_audio])

        timer2 = gr.Timer(1.0)
        def drain2():
            evs = jm.bus.drain()
            if not evs:
                return gr.update()
            lines = [f"[{e['estagio']}] {e['status']} {e['pct']:.0f}% - {e['msg']}" for e in evs]
            return "\n".join(lines)
        timer2.tick(drain2, outputs=progress)
