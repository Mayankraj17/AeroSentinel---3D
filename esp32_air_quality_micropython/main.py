"""
============================================================================
ESP32 Air Quality Monitor - MicroPython Edition (Sensor-Safe)
============================================================================
Works WITH or WITHOUT sensors connected.
  - If PMS5003/7003 is not connected → Shows "PM Sensor: Offline"
  - If MQ-135 is not connected → Shows raw ADC noise reading
  - Wi-Fi and timestamps always work regardless of sensors

Upload this as main.py once test_no_sensors.py passes all tests.
============================================================================
"""

import time
import json
import gc
import config
from pm_sensor import PMSensor
from mq135_sensor import MQ135Sensor
from wifi_manager import WiFiManager
from time_sync import TimeSync

# ============================================================================
# INITIALIZATION
# ============================================================================
print("\n" + "=" * 55)
print("  ESP32 AIR QUALITY MONITOR - MICROPYTHON EDITION")
print("=" * 55)

# ---------- Sensors (safe if not connected) ----------
sensors_available = {"pm": False, "gas": False}

# PM Sensor — will simply show "offline" if not physically connected
print(f"[Init] PM Sensor (UART{config.PMS_UART_ID}): Listening... (OK if not connected)")
pm_sensor = PMSensor(
    uart_id=config.PMS_UART_ID,
    rx_pin=config.PMS_RX_PIN,
    tx_pin=config.PMS_TX_PIN,
    baudrate=config.PMS_BAUD_RATE,
    timeout_ms=config.PMS_TIMEOUT_MS
)

# MQ-135 — reads ADC noise if not connected (won't crash)
print(f"[Init] MQ-135 (GPIO {config.MQ135_PIN}): Reading ADC... (noise is normal without sensor)")
mq135_sensor = MQ135Sensor(
    pin=config.MQ135_PIN,
    rl_kohm=config.MQ135_RL_KOHM,
    ro_clean_air_kohm=config.MQ135_RO_CLEAN_AIR_KOHM,
    vcc_supply=config.MQ135_VCC_SUPPLY,
    vref_esp32=config.MQ135_VREF_ESP32,
    samples=config.MQ135_SAMPLES,
    param_a=config.MQ135_PARAM_A,
    param_b=config.MQ135_PARAM_B
)

# ---------- Wi-Fi ----------
print("[Init] Wi-Fi Manager...")
wifi_manager = WiFiManager(
    ssid=config.WIFI_SSID,
    password=config.WIFI_PASSWORD,
    retry_interval_ms=config.WIFI_RETRY_INTERVAL_MS
)
wifi_manager.connect()

# ---------- Time ----------
print(f"[Init] NTP Time Sync ({config.NTP_SERVER})...")
time_sync = TimeSync(
    ntp_host=config.NTP_SERVER,
    gmt_offset_hours=config.GMT_OFFSET_HOURS
)

# ---------- Onboard LED for visual heartbeat ----------
from machine import Pin
led = Pin(33, Pin.OUT)  # Small red LED on back of ESP32-CAM (active LOW)
led.value(1)            # Start OFF

print("[Init] ✅ System ready. Entering measurement loop.\n")

# ============================================================================
# MQTT HOOK (unchanged — ready when you add a broker)
# ============================================================================
def handle_mqtt_transmission(json_payload_str):
    if not wifi_manager.is_connected():
        return
    if not config.MQTT_ENABLED:
        print(f"[MQTT Hook] Payload ready ({len(json_payload_str)} bytes)")
        return

# ============================================================================
# MAIN LOOP
# ============================================================================
last_publish_ticks = time.ticks_ms()
last_ntp_attempt_ticks = 0
reading_number = 0

while True:
    # 1. Background services
    wifi_manager.update()
    pm_sensor.update()

    # 2. Sync NTP when Wi-Fi connects
    now = time.ticks_ms()
    if wifi_manager.is_connected() and not time_sync.is_synced:
        if time.ticks_diff(now, last_ntp_attempt_ticks) >= 5000:
            last_ntp_attempt_ticks = now
            time_sync.sync()

    # 3. Periodic telemetry
    if time.ticks_diff(now, last_publish_ticks) >= config.SENSOR_READ_INTERVAL_MS:
        last_publish_ticks = now
        reading_number += 1

        # Blink the red LED as heartbeat
        led.value(0)  # ON

        # Read sensors (safe even if disconnected)
        gas_data = mq135_sensor.read()
        pm_data = pm_sensor.get_data()

        # Track if sensors come online
        if pm_data["sensor_valid"] and not sensors_available["pm"]:
            sensors_available["pm"] = True
            print("[Sensor] ✅ PM Sensor came online!")
        if gas_data["sensor_valid"] and gas_data["rs_kohm"] < 500 and not sensors_available["gas"]:
            sensors_available["gas"] = True
            print("[Sensor] ✅ MQ-135 Gas Sensor detected!")

        # Build payload
        payload = {
            "device_id": wifi_manager.get_device_id(),
            "timestamp": time_sync.get_iso8601_timestamp(),
            "time_synced": time_sync.is_synced,
            "epoch": time_sync.get_epoch(),
            "uptime_sec": time_sync.get_uptime_sec(),
            "reading_number": reading_number,
            "wifi": {
                "connected": wifi_manager.is_connected(),
                "ip": wifi_manager.get_ip()
            },
            "particulate_matter": {
                "sensor_valid": pm_data["sensor_valid"],
                "status": "Online" if pm_data["sensor_valid"] else "Offline (not connected)",
                "pm1_0_ug_m3": pm_data["pm1_0_env"] if pm_data["sensor_valid"] else None,
                "pm2_5_ug_m3": pm_data["pm2_5_env"] if pm_data["sensor_valid"] else None,
                "pm10_ug_m3": pm_data["pm10_env"] if pm_data["sensor_valid"] else None,
            },
            "gas_mq135": {
                "sensor_valid": gas_data["sensor_valid"],
                "status": gas_data["air_quality"] if gas_data["sensor_valid"] else "Offline (not connected)",
                "raw_adc": gas_data["raw_adc"],
                "voltage_mv": gas_data["voltage_mv"],
                "ppm_co2_equiv": gas_data["ppm_co2_equiv"] if gas_data["sensor_valid"] else None,
            }
        }

        # Serialize
        json_output = json.dumps(payload)

        # Print to Serial Monitor
        print(f"\n--- [READING #{reading_number}] ---")
        try:
            print(json.dumps(payload, indent=2))
        except (TypeError, ValueError):
            print(json_output)

        # Sensor status summary line
        pm_status = "✅ Online" if pm_data["sensor_valid"] else "❌ Not connected"
        gas_status = "✅ Online" if (gas_data["sensor_valid"] and gas_data["rs_kohm"] < 500) else "❌ Not connected"
        wifi_status = "✅ " + wifi_manager.get_ip() if wifi_manager.is_connected() else "❌ Offline"
        time_status = "✅ " + time_sync.get_iso8601_timestamp() if time_sync.is_synced else "⏳ Waiting for NTP"
        print(f"[Status] PM: {pm_status} | Gas: {gas_status} | WiFi: {wifi_status} | Time: {time_status}")
        print("---")

        # MQTT dispatch
        handle_mqtt_transmission(json_output)

        # LED off & cleanup
        led.value(1)  # OFF
        gc.collect()

    time.sleep_ms(config.LOOP_TICK_SLEEP_MS)
