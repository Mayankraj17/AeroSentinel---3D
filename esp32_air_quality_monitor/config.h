#pragma once

#include <Arduino.h>

// ============================================================================
// SYSTEM & SERIAL CONFIGURATION
// ============================================================================
constexpr uint32_t SERIAL_MONITOR_BAUD = 115200;
constexpr uint32_t SENSOR_READ_INTERVAL_MS = 5000;  // Publish / print interval in ms

// Device Identification
#define DEVICE_ID_PREFIX "ESP32-AQM-"

// ============================================================================
// WI-FI CONFIGURATION
// ============================================================================
// Replace with your local network credentials
constexpr const char* WIFI_SSID     = "YOUR_WIFI_SSID";
constexpr const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

constexpr uint32_t WIFI_RETRY_INTERVAL_MS = 10000; // Retry interval if disconnected
constexpr uint32_t WIFI_CONNECT_TIMEOUT_MS = 15000;

// ============================================================================
// NTP / TIME CONFIGURATION
// ============================================================================
constexpr const char* NTP_SERVER_PRIMARY   = "pool.ntp.org";
constexpr const char* NTP_SERVER_SECONDARY = "time.nist.gov";

// Timezone offset in seconds (e.g., UTC+0 = 0, UTC+5:30 = 19800, UTC-5 = -18000)
constexpr long GMT_OFFSET_SEC       = 0;     // UTC standard
constexpr int  DAYLIGHT_OFFSET_SEC  = 0;     // Daylight saving offset in seconds

// ============================================================================
// PMS5003 / PMS7003 SENSOR CONFIGURATION (UART / Serial2)
// ============================================================================
// Hardware UART2 pins on ESP32
// Connect ESP32 PMS_RX_PIN (GPIO 16) -> PMS Sensor TXD
// Connect ESP32 PMS_TX_PIN (GPIO 17) -> PMS Sensor RXD (Optional for passive mode)
constexpr int PMS_RX_PIN = 16;
constexpr int PMS_TX_PIN = 17;
constexpr uint32_t PMS_BAUD_RATE = 9600;
constexpr uint32_t PMS_READ_TIMEOUT_MS = 3000;

// ============================================================================
// MQ-135 GAS SENSOR CONFIGURATION (ADC)
// ============================================================================
// CRITICAL ESP32 NOTE:
// Always use ADC1 pins (GPIO 32, 33, 34, 35, 36, 39) when Wi-Fi is active.
// ADC2 pins (GPIO 0, 2, 4, 12, 13, 14, 15, 25, 26, 27) cannot be used while Wi-Fi is transmitting.
constexpr int MQ135_ANALOG_PIN = 34; // ADC1_CH6 (Input only, Wi-Fi safe)

// Circuit & Calibration constants
constexpr float MQ135_VREF_VOLTS        = 3.3f;   // ESP32 ADC reference voltage
constexpr float MQ135_RL_KOHM           = 10.0f;  // Load resistance on the breakout board (typically 10k or 1k)
constexpr float MQ135_RO_CLEAN_AIR_KOHM = 76.63f; // Sensor resistance in clean air (calibrate per unit)
constexpr float MQ135_VCC_SUPPLY        = 5.0f;   // Heater/circuit voltage supplied to sensor (typically 5V)
constexpr int   MQ135_ADC_SAMPLES       = 32;     // Multi-sampling count for noise filtering

// Approximation curve for CO2 equivalent: ppm = A * (Rs / R0) ^ B
constexpr float MQ135_PARAM_A = 116.6020682f;
constexpr float MQ135_PARAM_B = -2.769034857f;

// ============================================================================
// MQTT CONFIGURATION PLACEHOLDER (Ready for transmission)
// ============================================================================
constexpr bool MQTT_ENABLED            = false; // Set to true once PubSubClient is configured
constexpr const char* MQTT_BROKER      = "192.168.1.100";
constexpr int         MQTT_PORT        = 1883;
constexpr const char* MQTT_TOPIC_TELEMETRY = "home/air_quality/telemetry";
constexpr const char* MQTT_CLIENT_USER = "";
constexpr const char* MQTT_CLIENT_PASS = "";
