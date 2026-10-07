"""
Fire and Smoke Detection System — Main Entry Point
====================================================
CLI interface to train the model or run real-time detection.

Commands:
    python main.py train   --dataset <path>            Train the CNN model
    python main.py detect                               Detect fire via webcam
    python main.py detect  --source video.mp4           Detect fire in video file
    python main.py detect  --threshold 0.7              Custom threshold
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="[FIRE] Fire & Smoke Detection System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py train --dataset C:\forest fire
  python main.py detect
  python main.py detect --source fire_video.mp4
  python main.py detect --threshold 0.7
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ── Train command ──────────────────────────
    train_parser = subparsers.add_parser(
        "train", help="Train the fire detection model on your dataset"
    )
    train_parser.add_argument(
        "--dataset", type=str, required=True,
        help="Path to dataset folder (must contain 'fire/' and 'non_fire/' subfolders)"
    )

    # ── Detect command ─────────────────────────
    detect_parser = subparsers.add_parser(
        "detect", help="Run real-time fire detection"
    )
    detect_parser.add_argument(
        "--source", type=str, default="0",
        help="Video source: 0 for webcam (default), or path to video file"
    )
    detect_parser.add_argument(
        "--model", type=str, default=None,
        help="Path to trained .h5 model (default: fire_detection_model.h5)"
    )
    detect_parser.add_argument(
        "--threshold", type=float, default=0.6,
        help="Fire detection threshold 0.0-1.0 (default: 0.6)"
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        print("\n[ERROR] Please specify a command: 'train' or 'detect'")
        sys.exit(1)

    # ── Execute command ────────────────────────
    if args.command == "train":
        print("=" * 60)
        print("   [FIRE] FIRE & SMOKE DETECTION - TRAINING MODE")
        print("=" * 60)
        from train_model import train
        train(args.dataset)

    elif args.command == "detect":
        print("=" * 60)
        print("   [FIRE] FIRE & SMOKE DETECTION - REAL-TIME MODE")
        print("=" * 60)
        from fire_detector import run_detection, DEFAULT_MODEL_PATH

        source = int(args.source) if args.source.isdigit() else args.source
        model_path = args.model if args.model else DEFAULT_MODEL_PATH

        run_detection(
            source=source,
            model_path=model_path,
            threshold=args.threshold,
        )


if __name__ == "__main__":
    main()
