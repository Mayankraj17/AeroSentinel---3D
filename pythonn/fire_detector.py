"""
Fire and Smoke Detection — Real-Time Detector
===============================================
Uses a trained CNN model to detect fire/smoke in real-time video frames.

Features:
    - Webcam or video file input
    - Live annotated display with fire probability
    - Red alert overlay when fire is detected
    - Green safe indicator for normal conditions

Usage:
    python fire_detector.py                           # webcam
    python fire_detector.py --source video.mp4        # video file
    python fire_detector.py --threshold 0.7           # custom threshold
"""

import os
import sys
import time
import argparse
import cv2
import numpy as np
from tensorflow.keras.models import load_model

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
IMG_SIZE = 128
DEFAULT_MODEL_PATH = os.path.join(os.path.dirname(__file__), "fire_detection_model.h5")
DEFAULT_THRESHOLD = 0.6

# Colors (BGR format for OpenCV)
RED = (0, 0, 255)
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
ORANGE = (0, 140, 255)
DARK_RED = (0, 0, 180)
DARK_GREEN = (0, 120, 0)


def preprocess_frame(frame):
    """
    Preprocess a single video frame for CNN prediction.
    Resize to IMG_SIZE × IMG_SIZE, normalize to [0,1], add batch dimension.
    """
    resized = cv2.resize(frame, (IMG_SIZE, IMG_SIZE))
    normalized = resized.astype("float32") / 255.0
    return np.expand_dims(normalized, axis=0)


def draw_fire_alert(frame, confidence):
    """
    Draw a prominent FIRE DETECTED alert on the frame.
    Includes a semi-transparent red overlay, warning text, and confidence bar.
    """
    h, w = frame.shape[:2]

    # Semi-transparent red overlay at top
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 100), DARK_RED, -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

    # Warning icon triangle
    triangle_pts = np.array([(30, 80), (60, 20), (90, 80)], np.int32)
    cv2.fillPoly(frame, [triangle_pts], ORANGE)
    cv2.putText(frame, "!", (52, 72), cv2.FONT_HERSHEY_SIMPLEX, 1.5, BLACK, 3)

    # Main alert text
    cv2.putText(
        frame, "FIRE DETECTED!", (110, 55),
        cv2.FONT_HERSHEY_DUPLEX, 1.5, WHITE, 3, cv2.LINE_AA
    )

    # Confidence text
    conf_text = f"Confidence: {confidence * 100:.1f}%"
    cv2.putText(
        frame, conf_text, (110, 85),
        cv2.FONT_HERSHEY_SIMPLEX, 0.7, ORANGE, 2, cv2.LINE_AA
    )

    # Pulsing red border
    thickness = 4 + int(2 * np.sin(time.time() * 5))
    cv2.rectangle(frame, (0, 0), (w - 1, h - 1), RED, thickness)

    # Confidence bar at bottom
    bar_y = h - 30
    bar_width = int((w - 40) * confidence)
    cv2.rectangle(frame, (20, bar_y), (w - 20, bar_y + 20), WHITE, 1)
    cv2.rectangle(frame, (20, bar_y), (20 + bar_width, bar_y + 20), RED, -1)
    cv2.putText(
        frame, f"{confidence * 100:.0f}%", (w - 80, bar_y + 16),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE, 1, cv2.LINE_AA
    )

    return frame


def draw_safe_indicator(frame, confidence):
    """
    Draw a SAFE / No Fire indicator on the frame.
    Includes a semi-transparent green overlay and status text.
    """
    h, w = frame.shape[:2]

    # Semi-transparent green overlay at top
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 80), DARK_GREEN, -1)
    cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

    # Checkmark circle
    cv2.circle(frame, (50, 40), 25, GREEN, 2)
    cv2.putText(frame, "OK", (35, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, GREEN, 2)

    # Safe text
    cv2.putText(
        frame, "NO FIRE DETECTED", (90, 45),
        cv2.FONT_HERSHEY_DUPLEX, 1.0, WHITE, 2, cv2.LINE_AA
    )

    # Fire probability text (low value = safe)
    prob_text = f"Fire Prob: {confidence * 100:.1f}%"
    cv2.putText(
        frame, prob_text, (90, 70),
        cv2.FONT_HERSHEY_SIMPLEX, 0.6, GREEN, 1, cv2.LINE_AA
    )

    # Green border
    cv2.rectangle(frame, (0, 0), (w - 1, h - 1), GREEN, 2)

    return frame


def draw_fps(frame, fps):
    """Draw FPS counter in the bottom-left corner."""
    h = frame.shape[0]
    cv2.putText(
        frame, f"FPS: {fps:.1f}", (10, h - 10),
        cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 1, cv2.LINE_AA
    )
    return frame


def run_detection(source=0, model_path=DEFAULT_MODEL_PATH, threshold=DEFAULT_THRESHOLD):
    """
    Main detection loop.
    
    Args:
        source: 0 for webcam, or a file path for video
        model_path: path to the trained .h5 model
        threshold: fire probability threshold (0.0 – 1.0)
    """
    # ── Load model ──────────────────────────────
    if not os.path.exists(model_path):
        print(f"[ERROR] Model not found at: {model_path}")
        print("   Run 'python main.py train --dataset <path>' first to train the model.")
        sys.exit(1)

    print(f"[LOAD] Loading model from: {model_path}")
    model = load_model(model_path)
    print("[OK] Model loaded successfully!\n")

    # ── Open video source ───────────────────────
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open video source: {source}")
        sys.exit(1)

    source_name = "Webcam" if source == 0 else os.path.basename(str(source))
    print(f"[VIDEO] Source: {source_name}")
    print(f"[FIRE] Fire threshold: {threshold * 100:.0f}%")
    print(f"   Press 'q' to quit  |  Press 's' to save screenshot\n")

    # ── Detection variables ─────────────────────
    frame_count = 0
    fire_frame_count = 0
    fps = 0
    prev_time = time.time()
    screenshot_count = 0

    # ── Main loop ───────────────────────────────
    while True:
        ret, frame = cap.read()
        if not ret:
            if source != 0:
                print("[END] End of video file.")
            else:
                print("[ERROR] Failed to read from webcam.")
            break

        frame_count += 1

        # Preprocess and predict
        preprocessed = preprocess_frame(frame)
        prediction = model.predict(preprocessed, verbose=0)[0][0]

        # Draw appropriate overlay
        if prediction >= threshold:
            frame = draw_fire_alert(frame, prediction)
            fire_frame_count += 1
        else:
            frame = draw_safe_indicator(frame, prediction)

        # Calculate FPS
        current_time = time.time()
        fps = 1.0 / max(current_time - prev_time, 1e-6)
        prev_time = current_time
        frame = draw_fps(frame, fps)

        # Display
        window_name = "Fire & Smoke Detection"
        cv2.imshow(window_name, frame)

        # Key handling
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            print("\n[STOP] Detection stopped by user.")
            break
        elif key == ord("s"):
            screenshot_count += 1
            screenshot_path = os.path.join(
                os.path.dirname(__file__),
                f"screenshot_{screenshot_count}.png"
            )
            cv2.imwrite(screenshot_path, frame)
            print(f"[SAVED] Screenshot saved: {screenshot_path}")

    # ── Cleanup ─────────────────────────────────
    cap.release()
    cv2.destroyAllWindows()

    # ── Summary ─────────────────────────────────
    print(f"\n{'=' * 50}")
    print(f"  [SUMMARY] DETECTION SUMMARY")
    print(f"  Total frames analyzed : {frame_count}")
    print(f"  Fire detected frames  : {fire_frame_count}")
    if frame_count > 0:
        fire_pct = (fire_frame_count / frame_count) * 100
        print(f"  Fire detection rate   : {fire_pct:.1f}%")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real-time fire & smoke detection")
    parser.add_argument(
        "--source", type=str, default="0",
        help="Video source: 0 for webcam (default), or path to video file"
    )
    parser.add_argument(
        "--model", type=str, default=DEFAULT_MODEL_PATH,
        help="Path to trained .h5 model file"
    )
    parser.add_argument(
        "--threshold", type=float, default=DEFAULT_THRESHOLD,
        help="Fire detection threshold (0.0-1.0, default: 0.6)"
    )
    args = parser.parse_args()

    # Convert "0" string to int for webcam
    source = int(args.source) if args.source.isdigit() else args.source
    run_detection(source=source, model_path=args.model, threshold=args.threshold)
