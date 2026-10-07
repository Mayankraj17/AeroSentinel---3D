#include "wifi_manager.h"
#include "config.h"

WiFiManager::WiFiManager()
    : _ssid(nullptr),
      _password(nullptr),
      _wasConnected(false),
      _lastReconnectAttemptMs(0) {}

void WiFiManager::begin(const char* ssid, const char* password) {
    _ssid = ssid;
    _password = password;

    // Build unique device ID from MAC address
    uint8_t mac[6];
    WiFi.macAddress(mac);
    char devIdBuf[32];
    snprintf(devIdBuf, sizeof(devIdBuf), "%s%02X%02X%02X",
             DEVICE_ID_PREFIX, mac[3], mac[4], mac[5]);
    _deviceId = String(devIdBuf);

    Serial.printf("[WiFi] Device ID: %s\n", _deviceId.c_str());
    Serial.printf("[WiFi] Connecting to SSID: %s\n", _ssid);

    WiFi.mode(WIFI_STA);
    WiFi.setAutoReconnect(true);
    connect();
}

void WiFiManager::connect() {
    if (!_ssid || strlen(_ssid) == 0 || strcmp(_ssid, "YOUR_WIFI_SSID") == 0) {
        Serial.println("[WiFi] Warning: Wi-Fi credentials not configured in config.h. Running offline.");
        return;
    }

    WiFi.begin(_ssid, _password);
    _lastReconnectAttemptMs = millis();
}

void WiFiManager::update() {
    bool currentlyConnected = isConnected();

    if (currentlyConnected && !_wasConnected) {
        // Just connected!
        _wasConnected = true;
        Serial.println("\n[WiFi] Connected successfully!");
        Serial.printf("[WiFi] IP Address: %s\n", WiFi.localIP().toString().c_str());
        Serial.printf("[WiFi] Signal Strength (RSSI): %d dBm\n", WiFi.RSSI());
    } else if (!currentlyConnected && _wasConnected) {
        // Connection lost
        _wasConnected = false;
        Serial.println("\n[WiFi] Connection lost. Will attempt reconnect in background...");
        _lastReconnectAttemptMs = millis();
    } else if (!currentlyConnected) {
        // Not connected; check if retry timer expired
        if (millis() - _lastReconnectAttemptMs >= WIFI_RETRY_INTERVAL_MS) {
            _lastReconnectAttemptMs = millis();
            if (_ssid && strlen(_ssid) > 0 && strcmp(_ssid, "YOUR_WIFI_SSID") != 0) {
                Serial.println("[WiFi] Attempting reconnection...");
                WiFi.reconnect();
            }
        }
    }
}

bool WiFiManager::isConnected() const {
    return WiFi.status() == WL_CONNECTED;
}

int32_t WiFiManager::getRSSI() const {
    return isConnected() ? WiFi.RSSI() : 0;
}

String WiFiManager::getIpAddress() const {
    return isConnected() ? WiFi.localIP().toString() : String("0.0.0.0");
}

String WiFiManager::getMacAddress() const {
    return WiFi.macAddress();
}

String WiFiManager::getDeviceId() const {
    return _deviceId;
}
