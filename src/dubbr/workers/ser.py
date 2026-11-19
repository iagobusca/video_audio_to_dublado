"""Worker SER (audeering) - stub. Roda em venv ser."""
import argparse


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8011)
    args = ap.parse_args()
    # placeholder: servidor HTTP FastAPI real entra aqui
    print(f"[worker-ser] listening on {args.port}")
    import time
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
