"""CSS global da UI (modal de pipeline + barra de progresso)."""
MODAL_CSS = """
#pipeline-modal {
    position: fixed;
    inset: 0;
    z-index: 1000;
    background: rgba(0, 0, 0, 0.55);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
}
#pipeline-modal > .gr-column,
#pipeline-modal > div {
    background: var(--background-fill-primary);
    color: var(--body-text-color);
    border: 1px solid var(--border-color-primary);
    border-radius: 12px;
    padding: 20px;
    width: min(640px, 92vw);
    max-height: 85vh;
    overflow-y: auto;
    box-shadow: 0 12px 48px rgba(0, 0, 0, 0.45);
}
#pipeline-modal-close { min-width: 90px; }
.dubbr-progress {
    width: 100%;
    height: 10px;
    border-radius: 6px;
    background: var(--border-color-primary);
    overflow: hidden;
}
.dubbr-progress .bar {
    height: 100%;
    background: var(--color-accent);
    transition: width 0.3s;
}
"""
