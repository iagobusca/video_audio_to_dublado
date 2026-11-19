"""Worker TTS Chatterbox pt-br - stub."""
import argparse, time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8022)
    args = ap.parse_args()
    print(f"[worker-tts-chatterbox] listening on {args.port}")
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
