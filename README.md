# 🛰️ AeroSentinel 3D — Autonomous IoT Air Quality & AI Fire Sentinel

[![Platform: ESP32](https://img.shields.io/badge/Hardware-ESP32--CAM-blue.svg)](https://www.espressif.com/)
[![Firmware: MicroPython](https://img.shields.io/badge/Firmware-MicroPython%20v1.29-yellow.svg)](https://micropython.org/)
[![Protocol: MQTT](https://img.shields.io/badge/Telemetry-MQTT%203.1.1-orange.svg)](https://mqtt.org/)
[![Dashboard: Three.js](https://img.shields.io/badge/3D%20Mapping-Three.js%20WebGL-emerald.svg)](https://threejs.org/)
[![AI Model: TensorFlow/Keras](https://img.shields.io/badge/Computer%20Vision-CNN%20Fire%20Detection-red.svg)](https://tensorflow.org/)

An end-to-end edge-to-cloud environmental monitoring and optical fire detection platform. Designed for smart cities, industrial plants, and emergency evacuation management.

---

## 🌟 Key Highlights

- **Edge IoT Node (ESP32-CAM):** Multi-modal data acquisition collecting PM2.5, PM10, MQ-135 hazardous combustion gases, and video feed. Runs autonomous non-blocking MicroPython firmware with NTP real-time clock synchronization.
- **Low-Latency Cloud Telemetry (MQTT):** Formats standardized ISO-8601 JSON payloads and streams them wirelessly via HiveMQ public cloud broker in sub-second intervals.
- **3D Spatial Digital Twin (`dashboard_3d_air_quality.html`):** Interactive WebGL/Three.js 3D room visualization with orbit controls, dynamic volumetric smoke dispersion plumes, and real-time Chart.js telemetry graphs.
- **Dual-Verification Computer Vision AI:** Onboard CNN classifier (`fire_detection_model.h5`) cross-validates optical flame/smoke detection with chemical gas telemetry to prevent false alarms.

---

## 📁 Repository Structure

```
├── dashboard_3d_air_quality.html       # 🚀 Interactive 3D Digital Twin Web Dashboard (Three.js + MQTT)
│
├── esp32_air_quality_micropython/     # 🐍 MicroPython Firmware for ESP32-CAM
│   ├── main_mqtt_demo.py               # Complete firmware with cloud MQTT client & physics simulation
│   ├── pm_sensor.py                    # Plantower PMS5003 UART driver with checksum validation
│   ├── mq135_sensor.py                 # MQ-135 oversampled ADC driver & PPM calculation
│   ├── wifi_manager.py                 # Non-blocking Wi-Fi station controller
│   └── time_sync.py                    # NTP UTC clock synchronizer
│
├── esp32_air_quality_monitor/          # ⚡ Arduino C++ Production Project (PlatformIO / Arduino IDE)
│   ├── esp32_air_quality_monitor.ino
│   ├── config.h
│   └── platformio.ini
│
└── pythonn/                            # 👁️ Computer Vision Fire & Smoke Detection
    ├── fire_detector_mqtt.py           # Real-time OpenCV + CNN detector broadcasting MQTT alerts
    └── fire_detection_model.h5         # Pretrained Keras CNN model weights
```

---

## 🚀 Quick Start Guide

### 1. Flash the ESP32-CAM
1. Open [Thonny IDE](https://thonny.org/) and select **MicroPython (ESP32)**.
2. Open [`esp32_air_quality_micropython/main_mqtt_demo.py`](./esp32_air_quality_micropython/main_mqtt_demo.py).
3. Update `WIFI_SSID` and `WIFI_PASSWORD` on lines 26–27.
4. Save as **`main.py`** to your **MicroPython device** and reboot.

### 2. Launch the 3D Digital Twin
Simply double-click [`dashboard_3d_air_quality.html`](./dashboard_3d_air_quality.html) to open it in Chrome, Edge, or Firefox.  
The dashboard automatically connects to the cloud MQTT broker and visualizes live telemetry in 3D.

### 3. Run the AI Fire Detector
```bash
cd pythonn
python fire_detector_mqtt.py --source 0
```

---

## 👨‍💻 Author
- **Mayank Raj** ([@Mayankraj17](https://github.com/Mayankraj17))
