import time
import network
import ubinascii

class WiFiManager:
    def __init__(self, ssid, password, retry_interval_ms=10000):
        self.ssid = ssid
        self.password = password
        self.retry_interval_ms = retry_interval_ms
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.was_connected = False
        self.last_reconnect_ms = 0
        self.device_id = self._generate_device_id()

    def _generate_device_id(self):
        try:
            mac_bytes = self.wlan.config('mac')
            mac_hex = ubinascii.hexlify(mac_bytes).decode().upper()
            return f"ESP32-AQM-{mac_hex[-6:]}"
        except Exception:
            return "ESP32-AQM-DEV001"

    def connect(self):
        """Initiate non-blocking connection attempt."""
        if not self.ssid or self.ssid == "YOUR_WIFI_SSID":
            print("[WiFi] Notice: Wi-Fi credentials not configured. Running offline.")
            return

        print(f"[WiFi] Connecting to SSID '{self.ssid}' (Device: {self.device_id})...")
        self.wlan.connect(self.ssid, self.password)
        self.last_reconnect_ms = time.ticks_ms()

    def update(self):
        """Call frequently in the main loop to monitor state and handle reconnections."""
        currently_connected = self.wlan.isconnected()

        if currently_connected and not self.was_connected:
            self.was_connected = True
            ip_info = self.wlan.ifconfig()
            print("\n[WiFi] Connected successfully!")
            print(f"[WiFi] IP Address: {ip_info[0]}")
            print(f"[WiFi] Subnet:     {ip_info[1]}")
            print(f"[WiFi] Gateway:    {ip_info[2]}")
            print(f"[WiFi] DNS:        {ip_info[3]}")

        elif not currently_connected and self.was_connected:
            self.was_connected = False
            print("\n[WiFi] Connection lost. Will attempt reconnect in background...")
            self.last_reconnect_ms = time.ticks_ms()

        elif not currently_connected:
            now = time.ticks_ms()
            if time.ticks_diff(now, self.last_reconnect_ms) >= self.retry_interval_ms:
                self.last_reconnect_ms = now
                if self.ssid and self.ssid != "YOUR_WIFI_SSID":
                    print("[WiFi] Attempting reconnection...")
                    try:
                        self.wlan.connect(self.ssid, self.password)
                    except Exception as e:
                        print(f"[WiFi] Reconnect error: {e}")

    def is_connected(self):
        return self.wlan.isconnected()

    def get_ip(self):
        return self.wlan.ifconfig()[0] if self.wlan.isconnected() else "0.0.0.0"

    def get_device_id(self):
        return self.device_id
