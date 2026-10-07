#pragma once

#include <Arduino.h>

struct PMData {
    uint16_t pm1_0_standard;   // PM1.0 standard particle, CF=1 [ug/m3]
    uint16_t pm2_5_standard;   // PM2.5 standard particle, CF=1 [ug/m3]
    uint16_t pm10_standard;    // PM10 standard particle, CF=1 [ug/m3]

    uint16_t pm1_0_env;        // PM1.0 under atmospheric environment [ug/m3]
    uint16_t pm2_5_env;        // PM2.5 under atmospheric environment [ug/m3]
    uint16_t pm10_env;         // PM10 under atmospheric environment [ug/m3]

    uint16_t particles_0_3um;  // Particles > 0.3um in 0.1L of air
    uint16_t particles_0_5um;  // Particles > 0.5um in 0.1L of air
    uint16_t particles_1_0um;  // Particles > 1.0um in 0.1L of air
    uint16_t particles_2_5um;  // Particles > 2.5um in 0.1L of air
    uint16_t particles_5_0um;  // Particles > 5.0um in 0.1L of air
    uint16_t particles_10um;   // Particles > 10um in 0.1L of air

    bool isValid;              // True if frame checksum passed and within timeout
    uint32_t lastReadMs;       // Timestamp of the last valid reading
};

class PMSensor {
public:
    PMSensor();

    // Initialize UART interface with designated pins and baud rate
    void begin(int rxPin, int txPin, uint32_t baudRate = 9600);

    // Non-blocking parser: call frequently in the main loop()
    void update();

    // Retrieve the latest parsed data
    const PMData& getData() const;

    // Check if the sensor has valid, recent data
    bool isHealthy() const;

private:
    static constexpr size_t FRAME_LENGTH = 32;
    static constexpr uint8_t START_BYTE_1 = 0x42;
    static constexpr uint8_t START_BYTE_2 = 0x4D;

    enum ParserState {
        STATE_WAIT_HEADER_1,
        STATE_WAIT_HEADER_2,
        STATE_READ_PAYLOAD
    };

    HardwareSerial* _serial;
    ParserState _state;
    uint8_t _frameBuffer[FRAME_LENGTH];
    size_t _bytesReceived;
    PMData _data;

    void parseFrame();
    bool verifyChecksum(const uint8_t* buffer, size_t length);
};
