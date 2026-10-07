#pragma once

#include <Arduino.h>
#include <WiFi.h>

class WiFiManager {
public:
    WiFiManager();

    // Start Wi-Fi station mode with non-blocking management
    void begin(const char* ssid, const char* password);

    // Call regularly in loop() to maintain connection and handle reconnections
    void update();

    // Connection queries
    bool isConnected() const;
    int32_t getRSSI() const;
    String getIpAddress() const;
    String getMacAddress() const;
    String getDeviceId() const;

private:
    const char* _ssid;
    const char* _password;
    bool _wasConnected;
    uint32_t _lastReconnectAttemptMs;
    String _deviceId;

    void connect();
};
