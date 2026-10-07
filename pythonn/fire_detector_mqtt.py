"""
============================================================================
AI Fire & Smoke Detector with Live MQTT Telemetry Integration
============================================================================
Runs your trained CNN model (fire_detection_model.h5) on webcam or video.
When fire/smoke is detected, it instantly broadcasts an emergency alert
to the 3D AeroSentinel Dashboard via the public MQTT broker!
============================================================================
"""

import os
import sys
import time
import json
import argparse
import cv2
import numpy as np

# ──────────────────────────────────────────────
# Constants & Model Setup
# ──────────────────────────────────────────────
IMG_SIZE = 128
DEFAULT_MODEL_PATH = os.path.join(os.path.dirname(__file__), "fire_detection_model.h5")
DEFAULT_THRESHOLD = 0.65

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "smartcity/air_quality/node_01"

# Colors for OpenCV HUD
RED = (0, 0, 255)
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
DARK_RED = (0, 0, 180)
ORANGE = (0, 140, 255)

# Try importing paho-mqtt with fallback
try:
    import paho.mqtt.client as mqtt
    HAVE_PAHO = True
except ImportError:
    HAVE_PAHO = False

def init_mqtt():
    if not HAVE_PAHO:
        print("[MQTT] paho-mqtt not available. Running local visual mode only.")
        return None
    try:
        if hasattr(mqtt, 'CallbackAPIVersion'):
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="Python-Fire-Detector-AI")
        else:
            client = mqtt.Client(client_id="Python-Fire-Detector-AI")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        print(f"[MQTT] Connected to {MQTT_BROKER}! Broadcasting alerts on '{MQTT_TOPIC}'")
        return client
    except Exception as e:
        print(f"[MQTT] Connection failed: {e}")
        return None

def publish_hazard_alert(mqtt_client, confidence):
    if not mqtt_client:
        return
    payload = {
        "device_id": "CAMERA-AI-SENTINEL",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "particulate_matter": {
            "pm1_0_ug_m3": 115.0,
            "pm2_5_ug_m3": 192.4,
            "pm10_ug_m3": 348.0
        },
        "hazardous_gas_mq135": {
            "co2_ppm": 1640.0,
            "air_quality": "HAZARDOUS COMBUSTION"
        },
        "environment": {
            "aqi_index": 320,
            "temperature_c": 32.5,
            "humidity_percent": 36.0
        },
        "vision_ai": {
            "camera_model": "OV3660 + CNN Real-Time Classifier",
            "smoke_detected": True,
            "fire_hazard": True,
            "confidence": round(float(confidence), 3)
        }
    }
    try:
        mqtt_client.publish(MQTT_TOPIC, json.dumps(payload))
    except Exception as e:
        print(f"[MQTT] Publish error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Real-Time Fire Detector with MQTT")
    parser.add_argument("--source", type=str, default="0", help="Webcam index (0) or video file path")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD, help="Fire detection threshold")
    args = parser.parse_args()

    # Load Model
    from tensorflow.keras.models import load_model
    print(f"[Model] Loading CNN from {DEFAULT_MODEL_PATH}...")
    model = load_model(DEFAULT_MODEL_PATH)
    print("[Model] ✅ Model loaded successfully!")

    # Connect MQTT
    mqtt_client = init_mqtt()

    # Open Video Source
    src = int(args.source) if args.source.isdigit() else args.source
    cap = cv2.VideoCapture(src)

    last_mqtt_send = 0

    print("\n[Running] Video stream active. Press 'q' to quit.")
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Preprocess frame
        resized = cv2.resize(frame, (IMG_SIZE, IMG_SIZE))
        normalized = resized.astype("float32") / 255.0
        batch = np.expand_dims(normalized, axis=0)

        # Inference
        pred = model.predict(batch, verbose=0)[0][0]
        is_fire = pred >= args.threshold

        # Draw UI
        h, w = frame.shape[:2]
        if is_fire:
            # Red Alert Overlay
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, 80), DARK_RED, -1)
            cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
            cv2.putText(frame, "FIRE / SMOKE DETECTED!", (20, 50), cv2.FONT_HERSHEY_DUPLEX, 1.2, WHITE, 2)
            cv2.putText(frame, f"Conf: {pred*100:.1f}%", (w - 180, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, ORANGE, 2)

            # Send MQTT alert (throttled to once per second)
            now = time.time()
            if now - last_mqtt_send >= 1.0:
                last_mqtt_send = now
                publish_hazard_alert(mqtt_client, pred)
        else:
            cv2.putText(frame, f"Normal: {pred*100:.1f}%", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, GREEN, 2)

        cv2.imshow("AeroSentinel Vision AI", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    if mqtt_client:
        mqtt_client.loop_stop()

if __name__ == "__main__":
    main()
