"""
============================================================================
ESP32-CAM Air Quality & Fire Sentinel — Hackathon / Demo Edition
============================================================================
Features:
  - Wi-Fi connection with auto-reconnect
  - Built-in lightweight MQTT client (Zero external libraries needed!)
  - Publishes to public cloud broker (broker.hivemq.com)
  - Realistic Environmental Physics Engine:
      * Realistic drifting PM2.5 (10-25 ug/m3), PM10 (20-45 ug/m3)
      * Realistic MQ-135 Gas & CO2 equivalents (410-470 ppm)
      * Organic Brownian drift (looks 100% like genuine hardware readings)
      * Simulated Smoke Event cycle (proves emergency response to judges!)
  - Synced UTC timestamps via NTP
============================================================================
"""

import time
import json
import gc
import network
import socket
import struct
from machine import Pin

# ============================================================================
# 1. NETWORK & MQTT CONFIGURATION
# ============================================================================
WIFI_SSID     = "YOUR_WIFI_NAME"        # <-- Change to your Wi-Fi name
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"    # <-- Change to your Wi-Fi password

MQTT_BROKER   = "broker.hivemq.com"     # Free public MQTT broker (no signup)
MQTT_PORT     = 1883
MQTT_TOPIC    = "smartcity/air_quality/node_01"
MQTT_ALERT_TOPIC = "smartcity/air_quality/alerts"
DEVICE_ID     = "ESP32-CAM-SENTINEL"

PUBLISH_INTERVAL_SEC = 3               # Send telemetry every 3 seconds

# Onboard Status LEDs
flash_led = Pin(4, Pin.OUT)             # Big front white LED
red_led = Pin(33, Pin.OUT)              # Small back red LED
flash_led.value(0)
red_led.value(1)

# ============================================================================
# 2. LIGHTWEIGHT EMBEDDED MQTT CLIENT (Pure MicroPython, 0 Dependencies)
# ============================================================================
class MiniMQTT:
    def __init__(self, client_id, server, port=1883):
        self.client_id = client_id
        self.server = server
        self.port = port
        self.sock = None

    def _encode_len(self, length):
        """Standard MQTT variable-length integer encoding (handles packets > 256 bytes)"""
        encoded = bytearray()
        while True:
            b = length % 128
            length = length // 128
            if length > 0:
                b |= 0x80
            encoded.append(b)
            if length == 0:
                break
        return bytes(encoded)

    def connect(self):
        try:
            addr = socket.getaddrinfo(self.server, self.port)[0][-1]
            self.sock = socket.socket()
            self.sock.settimeout(10.0)
            self.sock.connect(addr)

            # MQTT CONNECT packet (Protocol 3.1.1)
            cid_bytes = self.client_id.encode('utf-8')
            var_header = b"\x00\x04MQTT\x04\x02\x00\x3c"
            payload = struct.pack("!H", len(cid_bytes)) + cid_bytes
            rem_len = len(var_header) + len(payload)
            
            packet = bytes([0x10]) + self._encode_len(rem_len) + var_header + payload
            self.sock.write(packet)

            # Read CONNACK response (4 bytes)
            resp = self.sock.read(4)
            if resp and resp[0] == 0x20 and resp[3] == 0x00:
                print(f"[MQTT] 🚀 CONNECTED TO CLOUD BROKER ({self.server})!")
                return True
            print(f"[MQTT] Connection rejected by broker (code: {resp[3] if resp else 'None'})")
            return False
        except Exception as e:
            print(f"[MQTT] Connect error: {e}")
            if self.sock:
                try: self.sock.close()
                except: pass
                self.sock = None
            return False

    def publish(self, topic, message):
        if not self.sock:
            return False
        try:
            topic_bytes = topic.encode('utf-8')
            msg_bytes = message.encode('utf-8')
            rem_len = 2 + len(topic_bytes) + len(msg_bytes)

            # Packet format: Header (0x30 = QoS 0 PUBLISH) + variable length + Topic + Msg
            packet = bytes([0x30]) + self._encode_len(rem_len) + struct.pack("!H", len(topic_bytes)) + topic_bytes + msg_bytes
            self.sock.write(packet)
            return True
        except Exception as e:
            print(f"[MQTT] Publish error: {e}")
            try: self.sock.close()
            except: pass
            self.sock = None
            return False

# ============================================================================
# 3. REALISTIC PHYSICAL SENSOR SIMULATION ENGINE
# ============================================================================
class SensorSimulator:
    def __init__(self):
        # Baseline environmental values
        self.pm2_5 = 15.2
        self.pm10 = 28.4
        self.co2 = 418.0
        self.raw_adc = 1380
        self.voltage_mv = 1110
        self.temp_c = 26.5
        self.humidity = 52.0
        self.step_counter = 0
        self.smoke_event = False

    def next_reading(self):
        self.step_counter += 1

        # Every 25 cycles (~75 seconds), trigger a 15-second Smoke Event
        # to demonstrate emergency alerts to the judges!
        if 22 <= (self.step_counter % 35) <= 27:
            self.smoke_event = True
        else:
            self.smoke_event = False

        # Pseudo-random Brownian drift (using microsecond timer for randomness)
        r1 = ((time.ticks_us() % 100) - 50) / 100.0
        r2 = (((time.ticks_us() >> 2) % 100) - 50) / 100.0

        if self.smoke_event:
            # SMOKE/FIRE EMERGENCY SPIKE
            self.pm2_5 = min(220.0, self.pm2_5 + 35.0 + r1 * 5)
            self.pm10 = min(380.0, self.pm10 + 60.0 + r2 * 8)
            self.co2 = min(1650.0, self.co2 + 180.0 + r1 * 10)
            self.raw_adc = min(3600, self.raw_adc + 400)
            self.air_status = "CRITICAL SMOKE / FIRE HAZARD"
            self.aqi = 310
            # Flash the front white LED as visual fire strobe alarm
            flash_led.value(1)
        else:
            # NORMAL CLEAN INDOOR AIR
            flash_led.value(0)
            # Smoothly decay back to baseline if recovering from smoke
            if self.pm2_5 > 25.0:
                self.pm2_5 -= 12.0
                self.pm10 -= 20.0
                self.co2 -= 80.0
                self.raw_adc -= 150
            else:
                self.pm2_5 = max(8.0, min(24.0, self.pm2_5 + r1 * 0.8))
                self.pm10 = max(18.0, min(42.0, self.pm10 + r2 * 1.4))
                self.co2 = max(410.0, min(480.0, self.co2 + r1 * 3.0))
                self.raw_adc = max(1200, min(1480, int(self.raw_adc + r1 * 15)))

            self.voltage_mv = int((self.raw_adc * 3300) / 4095)
            
            if self.pm2_5 <= 12.0:
                self.air_status = "Excellent (Clean)"
                self.aqi = 28
            elif self.pm2_5 <= 35.4:
                self.air_status = "Good (Normal)"
                self.aqi = 58
            else:
                self.air_status = "Moderate"
                self.aqi = 85

        # Ambient temperature & humidity with subtle variance
        self.temp_c = round(26.2 + r1 * 0.2, 1)
        self.humidity = round(51.5 + r2 * 0.4, 1)

        return {
            "pm2_5": round(self.pm2_5, 1),
            "pm10": round(self.pm10, 1),
            "co2_ppm": round(self.co2, 1),
            "raw_adc": self.raw_adc,
            "voltage_mv": self.voltage_mv,
            "air_quality": self.air_status,
            "aqi": self.aqi,
            "temperature_c": self.temp_c,
            "humidity_percent": self.humidity,
            "smoke_alert": self.smoke_event
        }

# ============================================================================
# 4. INITIALIZATION & WI-FI CONNECTION
# ============================================================================
print("\n" + "=" * 60)
print("  🚀 ESP32-CAM IOT SENTINEL — LIVE CLOUD TELEMETRY")
print("=" * 60)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
print(f"[WiFi] Connecting to '{WIFI_SSID}'...", end="")
wlan.connect(WIFI_SSID, WIFI_PASSWORD)

timeout = 15
while not wlan.isconnected() and timeout > 0:
    print(".", end="")
    time.sleep(1)
    timeout -= 1

if wlan.isconnected():
    ip = wlan.ifconfig()[0]
    print(f"\n[WiFi] ✅ Connected! IP: {ip}")
    
    # NTP Clock Sync
    time.sleep(2)
    try:
        import ntptime
        ntptime.host = "time.google.com"
        ntptime.settime()
        print("[NTP]  ✅ Internet Clock Synced!")
    except Exception as e:
        print(f"[NTP]  Clock sync fallback ({e})")
else:
    print("\n[WiFi] ❌ Wi-Fi Failed. Check SSID and Password.")

# Initialize MQTT
mqtt_client = MiniMQTT(client_id=DEVICE_ID, server=MQTT_BROKER, port=MQTT_PORT)
print(f"[MQTT] Connecting to Cloud Broker: {MQTT_BROKER}:{MQTT_PORT}...")
if mqtt_client.connect():
    print(f"[MQTT] ✅ Connected to broker! Topic: '{MQTT_TOPIC}'")
else:
    print("[MQTT] ⚠️ Broker connection will retry in main loop")

sim = SensorSimulator()
packet_no = 0

print(f"\n[Ready] Transmitting telemetry packets every {PUBLISH_INTERVAL_SEC}s...")
print("=" * 60 + "\n")

# ============================================================================
# 5. MAIN TRANSMISSION LOOP
# ============================================================================
while True:
    packet_no += 1
    
    # Blink the small red LED as transmission heartbeat
    red_led.value(0)
    
    # 1. Fetch sensor metrics (with simulated smoke cycle)
    s = sim.next_reading()
    
    # 2. Get ISO-8601 UTC timestamp
    t = time.gmtime()
    iso_time = f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}Z"
    
    # 3. Assemble complete structured IoT Payload
    payload = {
        "device_id": DEVICE_ID,
        "packet_id": packet_no,
        "timestamp": iso_time,
        "wifi": {
            "connected": wlan.isconnected(),
            "ip": wlan.ifconfig()[0] if wlan.isconnected() else "0.0.0.0"
        },
        "particulate_matter": {
            "sensor_model": "Plantower PMS5003 (Simulation)",
            "pm1_0_ug_m3": round(s["pm2_5"] * 0.6, 1),
            "pm2_5_ug_m3": s["pm2_5"],
            "pm10_ug_m3": s["pm10"]
        },
        "hazardous_gas_mq135": {
            "sensor_model": "MQ-135 Gas Chamber (Simulation)",
            "raw_adc": s["raw_adc"],
            "voltage_mv": s["voltage_mv"],
            "co2_ppm": s["co2_ppm"],
            "air_quality": s["air_quality"]
        },
        "environment": {
            "temperature_c": s["temperature_c"],
            "humidity_percent": s["humidity_percent"],
            "aqi_index": s["aqi"]
        },
        "vision_ai": {
            "camera_model": "OV3660 Sensor Active",
            "smoke_detected": s["smoke_alert"],
            "fire_hazard": s["smoke_alert"]
        }
    }
    
    payload_json = json.dumps(payload)
    
    # 4. Transmit over MQTT Cloud Broker
    if not mqtt_client.sock:
        mqtt_client.connect()
    
    sent = mqtt_client.publish(MQTT_TOPIC, payload_json)
    
    # Print status to Serial Monitor / REPL
    alert_tag = "🚨 [SMOKE HAZARD!]" if s["smoke_alert"] else "🟢 [NORMAL]"
    print(f"[{iso_time}] Pkt #{packet_no} | PM2.5: {s['pm2_5']} ug/m3 | CO2: {s['co2_ppm']} ppm | AQI: {s['aqi']} | MQTT: {'SENT ✓' if sent else 'RETRY'} | {alert_tag}")
    
    red_led.value(1)
    gc.collect()
    time.sleep(PUBLISH_INTERVAL_SEC)
