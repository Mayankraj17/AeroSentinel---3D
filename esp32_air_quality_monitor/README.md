# ESP32 Production Air Quality Monitoring Node

A modular, production-ready Arduino C++ firmware for the **ESP32** designed to monitor ambient air quality. It reads particulate matter data from a **Plantower PMS5003 / PMS7003** sensor via hardware UART (`Serial2`), measures gas concentrations using an **MQ-135** sensor via ESP32 ADC1, packages telemetry into structured **JSON** with synchronized **NTP ISO-8601 timestamps**, outputs to the Serial Monitor, and provides a non-blocking Wi-Fi management loop ready for MQTT transmission.

---

## 📁 Project Architecture

```
esp32_air_quality_monitor/
├── esp32_air_quality_monitor.ino  # Main application entry point & execution loop
├── config.h                       # Hardware pin definitions, Wi-Fi credentials & tuning constants
├── pm_sensor.h / .cpp             # Non-blocking UART driver with 16-bit frame checksum validation
├── mq135_sensor.h / .cpp          # Oversampled ADC sampling, Rs/R0 curve, and CO2-equiv calculation
├── time_sync.h / .cpp             # Native ESP32 SNTP sync with ISO-8601 formatting
├── wifi_manager.h / .cpp          # Non-blocking Wi-Fi station controller with auto-reconnect
├── payload_builder.h / .cpp       # ArduinoJson payload serialization (v6/v7 compatible)
├── platformio.ini                 # PlatformIO configuration for ESP32
└── README.md                      # Hardware wiring, calibration, and documentation
```

---

## 🔌 Hardware Wiring & Pinout

### 1. Plantower PMS5003 / PMS7003 (Laser Dust Sensor)
> **Note:** The PMS5003/7003 requires 5V power for its internal laser diode and fan, but its logic output (TX) is 3.3V compatible with the ESP32.

| PMS Pin | Description | ESP32 Pin | Notes |
|---|---|---|---|
| **Pin 1 (VCC)** | Power Supply | `5V` (or `VIN` / `VBUS`) | Must provide stable 5V |
| **Pin 2 (GND)** | Ground | `GND` | Common ground |
| **Pin 4 (RXD)** | Data Receive | `GPIO 17` (`TX2`) | Optional (used to send sleep/wake commands) |
| **Pin 5 (TXD)** | Data Transmit | `GPIO 16` (`RX2`) | **Required**: 9600 baud UART stream |
| **Pin 3 (SET)** | Working Mode | Pull-up to 3.3V / Leave Floating | High: Active mode, Low: Sleep mode |
| **Pin 6 (RESET)**| Reset Pin | Pull-up to 3.3V / Leave Floating | Active low reset |

### 2. MQ-135 (Hazardous Gas & Air Quality Sensor)
> **CRITICAL ESP32 HARDWARE NOTE:**  
> On the ESP32, **ADC2** (GPIO 0, 2, 4, 12-15, 25-27) is shared with the Wi-Fi subsystem and **cannot be sampled while Wi-Fi is active**.  
> This firmware uses **ADC1 Pin GPIO 34**, which is an input-only ADC pin completely independent of Wi-Fi.

| MQ-135 Pin | Description | ESP32 Pin | Notes |
|---|---|---|---|
| **VCC** | 5V Heater Supply | `5V` (or `VIN`) | MQ heater coils require 5V to maintain 150°C |
| **GND** | Ground | `GND` | Common ground |
| **AOUT** | Analog Output Voltage | `GPIO 34` | Connect through voltage divider if AOUT exceeds 3.3V |
| **DOUT** | Digital Threshold | *Unconnected* | Not used |

> ⚠️ **Voltage Protection Tip:** If the MQ-135 analog output can exceed 3.3V in high gas concentrations, place a simple resistive divider (e.g., $10\,\text{k}\Omega$ and $20\,\text{k}\Omega$) or a 3.3V Zener diode between `AOUT` and `GPIO 34`.

---

## ⚙️ Configuration (`config.h`)

Open [`config.h`](file:///c:/Users/VICTUS/c++/esp32_air_quality_monitor/config.h) and set your Wi-Fi credentials and parameters:

```cpp
// Wi-Fi Credentials
constexpr const char* WIFI_SSID     = "YOUR_WIFI_SSID";
constexpr const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// Telemetry publication rate
constexpr uint32_t SENSOR_READ_INTERVAL_MS = 5000; // Every 5 seconds

// Timezone offset in seconds (e.g., UTC+0 = 0, UTC+5:30 = 19800, UTC-5 = -18000)
constexpr long GMT_OFFSET_SEC = 0;
```

---

## 📊 Telemetry JSON Payload Structure

The firmware generates telemetry in standard JSON:

```json
{
  "device_id": "ESP32-AQM-8C45A1",
  "timestamp": "2026-10-06T12:45:30Z",
  "time_synced": true,
  "epoch": 1791290730,
  "uptime_sec": 42,
  "wifi": {
    "connected": true,
    "rssi_dbm": -58,
    "ip": "192.168.1.142"
  },
  "particulate_matter": {
    "sensor_valid": true,
    "pm1_0_ug_m3": 8,
    "pm2_5_ug_m3": 15,
    "pm10_ug_m3": 28,
    "pm2_5_cf1": 15,
    "particle_counts_0_1L": {
      "gt_0_3um": 1280,
      "gt_0_5um": 340,
      "gt_2_5um": 24
    }
  },
  "gas_mq135": {
    "sensor_valid": true,
    "raw_adc": 1350,
    "voltage_mv": 1088,
    "rs_kohm": 35.95,
    "rs_ro_ratio": 0.469,
    "ppm_co2_equiv": 412.3,
    "air_quality": "Excellent (Clean Outdoor Air)"
  }
}
```

---

## 🛠️ Calibration of the MQ-135 Sensor

1. **Burn-in Phase:** Power the MQ-135 sensor continuously for at least 24–48 hours before initial calibration so the chemical sensing layer stabilizes.
2. **Determine $R_0$ in Clean Air:** Place the node in fresh outdoor air (baseline $\sim 415\,\text{ppm}\ \text{CO}_2$).
3. You can invoke the built-in calibration helper:
   ```cpp
   float r0 = mq135Sensor.calibrateR0InCleanAir(50, 100);
   Serial.printf("Calibrated R0: %.2f kOhm\n", r0);
   ```
4. Copy the measured $R_0$ value into `MQ135_RO_CLEAN_AIR_KOHM` in [`config.h`](file:///c:/Users/VICTUS/c++/esp32_air_quality_monitor/config.h).

---

## 🚀 Building & Flashing

### Option A: Using PlatformIO (Recommended)
1. Open this directory in VS Code with PlatformIO extension installed.
2. PlatformIO will automatically install the `ArduinoJson` library specified in [`platformio.ini`](file:///c:/Users/VICTUS/c++/esp32_air_quality_monitor/platformio.ini).
3. Click **Build** (`Ctrl+Alt+B`) and **Upload** (`Ctrl+Alt+U`).
4. Open the Serial Monitor at `115200` baud.

### Option B: Using Arduino IDE
1. Open the [Arduino IDE](https://www.arduino.cc/en/software).
2. Install the **ESP32** board package (`esp32 by Espressif Systems`) via Boards Manager.
3. Open Library Manager (`Ctrl+Shift+I`) and install:
   - **ArduinoJson** (version 7.x or 6.x)
4. Open [`esp32_air_quality_monitor.ino`](file:///c:/Users/VICTUS/c++/esp32_air_quality_monitor/esp32_air_quality_monitor.ino).
5. Select board **ESP32 Dev Module** and the correct COM port.
6. Click **Upload**.

---

## 📡 MQTT Transmission Integration

The project is structured with an MQTT dispatch hook in [`esp32_air_quality_monitor.ino`](file:///c:/Users/VICTUS/c++/esp32_air_quality_monitor/esp32_air_quality_monitor.ino#L96):

```cpp
void handleMqttTransmission(const String& jsonPayload) {
    if (!wifiManager.isConnected()) return;

    if (!MQTT_ENABLED) {
        Serial.printf("[MQTT Hook] Ready to publish (%u bytes) to topic '%s'\n",
                      jsonPayload.length(), MQTT_TOPIC_TELEMETRY);
        return;
    }

    // PubSubClient publish call:
    // mqttClient.publish(MQTT_TOPIC_TELEMETRY, jsonPayload.c_str());
}
```

To enable MQTT with **PubSubClient**:
1. In `platformio.ini` (or Arduino IDE Library Manager), install `knolleary/PubSubClient`.
2. In `config.h`, set `MQTT_ENABLED = true` and provide your broker IP and topic.
3. Uncomment the client definition in `handleMqttTransmission`.
