"""CSS global da UI (modal de pipeline + barra de progresso)."""
MODAL_CSS = """
#pipeline-modal {
    border: 1px solid var(--border-color-primary);
    border-radius: 12px;
    padding: 16px;
    margin-top: 12px;
    background: var(--background-fill-secondary);
}
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
