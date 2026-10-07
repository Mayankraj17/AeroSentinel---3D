# ESP32 Air Quality Monitor (MicroPython Edition)

A complete, beginner-friendly yet production-structured **Python** implementation for the ESP32 using **MicroPython**.

---

## 📁 Project Structure

```
esp32_air_quality_micropython/
├── boot.py          # Executes on cold boot (disables debug spam, initializes GC)
├── main.py          # Main application loop, JSON packaging & MQTT dispatch hook
├── config.py        # Central configuration (pins, Wi-Fi credentials, thresholds)
├── pm_sensor.py     # Non-blocking UART/Serial2 driver with 16-bit checksum validation
├── mq135_sensor.py  # Oversampled ADC reading, Rs/R0 curve, and CO2-equiv calculations
├── wifi_manager.py  # Non-blocking Wi-Fi station controller with background auto-reconnect
├── time_sync.py     # NTP real-time clock sync and ISO-8601 formatting
└── README.md        # Hardware wiring, flashing guide, and Python vs C++ comparison
```

---

## ⚡ Quick Start: How to Run Python on ESP32

To run Python on an ESP32, you install **MicroPython** (a lightweight Python 3 implementation optimized for microcontrollers).

### Step 1: Install Thonny IDE (Easiest Method)
1. Download and install [Thonny IDE](https://thonny.org/).
2. Plug your ESP32 into your computer via a USB cable.

### Step 2: Flash MicroPython onto the ESP32
1. In Thonny, go to **Tools** > **Options** > **Interpreter**.
2. Select **MicroPython (ESP32)** from the dropdown.
3. Click the link in the bottom-right: **Install or update MicroPython**.
4. Select your ESP32 COM port and click **Install**. (Thonny downloads and flashes the official MicroPython firmware automatically in ~1 minute).

### Step 3: Upload the Python Files
1. Open this folder (`esp32_air_quality_micropython`) in Thonny.
2. Edit [`config.py`](file:///c:/Users/VICTUS/c++/esp32_air_quality_micropython/config.py) with your Wi-Fi name and password.
3. Select all `.py` files (`boot.py`, `main.py`, `config.py`, `pm_sensor.py`, `mq135_sensor.py`, `wifi_manager.py`, `time_sync.py`), right-click, and choose **Upload to /**.
4. Press the **EN / RST** button on your ESP32 (or press `Ctrl+D` in Thonny to soft-reboot).
5. The terminal (REPL) will immediately output the formatted telemetry JSON!

---

## 🔌 Hardware Wiring & Pinout

| Sensor | Sensor Pin | ESP32 Pin | Notes |
|---|---|---|---|
| **PMS5003 / 7003** | `VCC` | `5V` (or `VIN`) | Sensor laser & fan require 5V |
| | `GND` | `GND` | Common ground |
| | `TXD` | `GPIO 16` (`RX2`) | UART2 Receive |
| | `RXD` | `GPIO 17` (`TX2`) | UART2 Transmit |
| **MQ-135** | `VCC` | `5V` (or `VIN`) | Heater coil requires 5V |
| | `GND` | `GND` | Common ground |
| | `AOUT` | `GPIO 34` | **ADC1** pin (Wi-Fi safe) |

---

## 📡 MQTT Integration (MicroPython)

To publish over MQTT, install the official MicroPython `umqtt.simple` package:
1. In Thonny: **Tools** > **Manage packages...** > search for `micropython-umqtt.simple` > **Install**.
2. Set `MQTT_ENABLED = True` in [`config.py`](file:///c:/Users/VICTUS/c++/esp32_air_quality_micropython/config.py).
3. The hook in [`main.py`](file:///c:/Users/VICTUS/c++/esp32_air_quality_micropython/main.py#L77) is pre-configured to connect and publish.
