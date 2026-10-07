# ============================================================================
# ESP32 Air Quality Monitor - Configuration (MicroPython)
# ============================================================================

# System & Timing
DEVICE_ID_PREFIX = "ESP32-AQM-"
SENSOR_READ_INTERVAL_MS = 5000     # Read & telemetry interval (5 seconds)
LOOP_TICK_SLEEP_MS = 50            # Background loop poll interval

# Wi-Fi Credentials
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"
WIFI_RETRY_INTERVAL_MS = 10000     # Reconnect retry interval if disconnected

# NTP Configuration
NTP_SERVER = "pool.ntp.org"
GMT_OFFSET_HOURS = 0               # UTC standard (set e.g. 5.5 for India, -5 for US EST)

# Hardware Pins
# PMS5003 / PMS7003 UART (UART2)
# Connect ESP32 Pin 16 (RX) -> Sensor TXD
# Connect ESP32 Pin 17 (TX) -> Sensor RXD
PMS_UART_ID = 2
PMS_RX_PIN = 16
PMS_TX_PIN = 17
PMS_BAUD_RATE = 9600
PMS_TIMEOUT_MS = 3000

# MQ-135 Gas Sensor (ADC)
# Use ADC1 pins (GPIO 32, 33, 34, 35, 36, 39) - safe with active Wi-Fi!
MQ135_PIN = 34
MQ135_RL_KOHM = 10.0               # Load resistance on breakout (typically 10k or 1k)
MQ135_RO_CLEAN_AIR_KOHM = 76.63    # Calibrated sensor resistance in clean air
MQ135_VCC_SUPPLY = 5.0             # Sensor heating/supply voltage (V)
MQ135_VREF_ESP32 = 3.3             # ESP32 ADC max voltage reference (V)
MQ135_SAMPLES = 32                 # Number of ADC oversamples for noise filtering

# MQ-135 CO2 curve coefficients: ppm = A * (Rs / R0) ^ B
MQ135_PARAM_A = 116.6020682
MQ135_PARAM_B = -2.769034857

# MQTT Configuration (Optional / Plug-and-Play)
MQTT_ENABLED = False               # Set to True when ready to publish to broker
MQTT_BROKER = "192.168.1.100"
MQTT_PORT = 1883
MQTT_TOPIC_TELEMETRY = "home/air_quality/telemetry"
MQTT_CLIENT_USER = None
MQTT_CLIENT_PASS = None
