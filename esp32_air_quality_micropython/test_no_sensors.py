"""
============================================================
  FIRST TEST SCRIPT — Run this to verify your setup works!
============================================================
  No sensors needed. This just proves:
    1. Your wiring is correct
    2. MicroPython is running
    3. Wi-Fi can connect
    4. Serial Monitor is working

  Upload ONLY this file as main.py to test.
============================================================
"""

import time
import gc

print("\n" + "=" * 50)
print("  🎉 HELLO! YOUR ESP32-CAM IS ALIVE!")
print("=" * 50)
print()

# -----------------------------------------------------------
# TEST 1: Basic Info
# -----------------------------------------------------------
print("[TEST 1] Basic System Info")
print(f"  Free RAM  : {gc.mem_free():,} bytes")
print(f"  Used RAM  : {gc.mem_alloc():,} bytes")
print()

# -----------------------------------------------------------
# TEST 2: Blink the onboard LED (GPIO 4 = Flash LED on ESP32-CAM)
# -----------------------------------------------------------
from machine import Pin

# GPIO 4 = The big white Flash LED on the front of your ESP32-CAM
# GPIO 33 = The small red LED on the back (active LOW on most boards)
flash_led = Pin(4, Pin.OUT)
red_led = Pin(33, Pin.OUT)

print("[TEST 2] Blinking the Flash LED 3 times...")
print("  (Look at the bright white LED on the front of your board!)")
for i in range(3):
    flash_led.value(1)   # ON
    time.sleep(0.3)
    flash_led.value(0)   # OFF
    time.sleep(0.3)
    print(f"  Blink {i + 1}/3 ✓")
print()

# -----------------------------------------------------------
# TEST 3: Try connecting to Wi-Fi
# -----------------------------------------------------------
print("[TEST 3] Wi-Fi Connection Test")

WIFI_SSID = "YOUR_WIFI_SSID"        # <-- Change this to your Wi-Fi name
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"  # <-- Change this to your Wi-Fi password

if WIFI_SSID == "YOUR_WIFI_SSID":
    print("  ⚠️  Wi-Fi credentials not set yet (that's OK for now!)")
    print("  ⚠️  Edit this file and replace YOUR_WIFI_SSID with your Wi-Fi name")
    print("  ⚠️  Skipping Wi-Fi test...")
    wifi_ok = False
else:
    import network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    print(f"  Connecting to '{WIFI_SSID}'...", end="")
    timeout = 15
    while not wlan.isconnected() and timeout > 0:
        print(".", end="")
        time.sleep(1)
        timeout -= 1

    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print(f"\n  ✅ Connected! IP Address: {ip}")
        wifi_ok = True
    else:
        print(f"\n  ❌ Could not connect. Check SSID and password.")
        wifi_ok = False
print()

# -----------------------------------------------------------
# TEST 4: Read the ADC pin (will show random noise without sensor)
# -----------------------------------------------------------
from machine import ADC

print("[TEST 4] ADC Pin Test (No MQ-135 sensor needed)")
adc = ADC(Pin(2))  # GPIO 2 is available on ESP32-CAM
adc.atten(ADC.ATTN_11DB)
reading = adc.read()
print(f"  Raw ADC value (GPIO 2): {reading}  (random noise = normal without sensor)")
print()

# -----------------------------------------------------------
# RESULT SUMMARY
# -----------------------------------------------------------
print("=" * 50)
print("  📋 TEST RESULTS SUMMARY")
print("=" * 50)
print(f"  ✅ MicroPython is running")
print(f"  ✅ Serial Monitor is working (you can see this!)")
print(f"  ✅ LED blink worked (did you see it flash?)")
if WIFI_SSID != "YOUR_WIFI_SSID":
    print(f"  {'✅' if wifi_ok else '❌'} Wi-Fi {'connected' if wifi_ok else 'FAILED'}")
else:
    print(f"  ⏭️  Wi-Fi skipped (credentials not set)")
print(f"  ✅ ADC reading: {reading}")
print("=" * 50)
print()

# -----------------------------------------------------------
# Keep running: Print a heartbeat every 3 seconds
# -----------------------------------------------------------
print("Now printing a heartbeat every 3 seconds to prove the board is running.")
print("Press Ctrl+C in Thonny to stop.\n")

count = 0
while True:
    count += 1
    uptime = count * 3
    free_ram = gc.mem_free()
    print(f"  💓 Heartbeat #{count} | Uptime: {uptime}s | Free RAM: {free_ram:,} bytes")
    
    # Blink the small red LED as a heartbeat indicator
    red_led.value(0)  # ON (active LOW)
    time.sleep(0.1)
    red_led.value(1)  # OFF
    
    gc.collect()
    time.sleep(2.9)
