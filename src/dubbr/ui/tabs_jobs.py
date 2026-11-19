"""Aba Jobs: historico (ESPEC 4)."""
import gradio as gr


def build(jm):
    with gr.Tab("Jobs"):
        table = gr.Dataframe(headers=["id", "entrada", "preset", "status", "criado"],
                            value=[], interactive=False)
        with gr.Row():
            jid = gr.Textbox(label="Job id")
            btn_resume = gr.Button("Retomar")
            btn_cancel = gr.Button("Cancelar")
        log = gr.Textbox(label="Log", lines=4)

        def refresh():
            rows = []
            for j in jm.list_jobs():
                rows.append([j["id"], j["entrada"], j["preset"], j["status"], j["criado"]])
            return rows

        def do_resume(j):
            jm.resume(j)
            return f"retomado {j}"

        def do_cancel(j):
            jm.cancel(j)
            return f"cancelado {j}"

        btn_resume.click(do_resume, inputs=[jid], outputs=log)
        btn_cancel.click(do_cancel, inputs=[jid], outputs=log)
        timer = gr.Timer(2.0)
        timer.tick(refresh, outputs=table)
    return
