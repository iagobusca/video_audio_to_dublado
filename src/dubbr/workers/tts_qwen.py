"""Worker TTS Qwen3 - stub (qwen-tts / qwentts.cpp)."""
import argparse, time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8021)
    args = ap.parse_args()
    print(f"[worker-tts-qwen] listening on {args.port}")
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
