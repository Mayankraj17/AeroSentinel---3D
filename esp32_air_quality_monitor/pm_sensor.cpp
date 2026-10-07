#include "pm_sensor.h"
#include "config.h"

PMSensor::PMSensor()
    : _serial(&Serial2),
      _state(STATE_WAIT_HEADER_1),
      _bytesReceived(0) {
    memset(&_data, 0, sizeof(PMData));
    _data.isValid = false;
}

void PMSensor::begin(int rxPin, int txPin, uint32_t baudRate) {
    // Hardware Serial2 initialization on ESP32 with custom GPIO pins
    _serial->begin(baudRate, SERIAL_8N1, rxPin, txPin);
    _state = STATE_WAIT_HEADER_1;
    _bytesReceived = 0;
}

void PMSensor::update() {
    // Process all currently available bytes from the UART buffer
    while (_serial->available() > 0) {
        uint8_t incomingByte = _serial->read();

        switch (_state) {
            case STATE_WAIT_HEADER_1:
                if (incomingByte == START_BYTE_1) {
                    _frameBuffer[0] = incomingByte;
                    _bytesReceived = 1;
                    _state = STATE_WAIT_HEADER_2;
                }
                break;

            case STATE_WAIT_HEADER_2:
                if (incomingByte == START_BYTE_2) {
                    _frameBuffer[1] = incomingByte;
                    _bytesReceived = 2;
                    _state = STATE_READ_PAYLOAD;
                } else if (incomingByte == START_BYTE_1) {
                    // Could be the real start byte if previous was spurious
                    _bytesReceived = 1;
                    _state = STATE_WAIT_HEADER_2;
                } else {
                    _bytesReceived = 0;
                    _state = STATE_WAIT_HEADER_1;
                }
                break;

            case STATE_READ_PAYLOAD:
                _frameBuffer[_bytesReceived++] = incomingByte;

                if (_bytesReceived >= FRAME_LENGTH) {
                    if (verifyChecksum(_frameBuffer, FRAME_LENGTH)) {
                        parseFrame();
                    } else {
                        // Checksum mismatch; discard frame
                        _data.isValid = false;
                    }
                    // Reset parser for subsequent packet
                    _bytesReceived = 0;
                    _state = STATE_WAIT_HEADER_1;
                }
                break;
        }
    }

    // Invalidate stale data if sensor stops reporting
    if (_data.isValid && (millis() - _data.lastReadMs > PMS_READ_TIMEOUT_MS)) {
        _data.isValid = false;
    }
}

bool PMSensor::verifyChecksum(const uint8_t* buffer, size_t length) {
    if (length < FRAME_LENGTH) return false;

    // Checksum is the sum of bytes 0 through 29
    uint16_t computedChecksum = 0;
    for (size_t i = 0; i < 30; ++i) {
        computedChecksum += buffer[i];
    }

    // Packet checksum is stored at bytes 30 (high) and 31 (low)
    uint16_t expectedChecksum = (static_cast<uint16_t>(buffer[30]) << 8) | buffer[31];

    return (computedChecksum == expectedChecksum);
}

void PMSensor::parseFrame() {
    // Bytes 4-9: Standard particles (CF=1)
    _data.pm1_0_standard = (static_cast<uint16_t>(_frameBuffer[4]) << 8) | _frameBuffer[5];
    _data.pm2_5_standard = (static_cast<uint16_t>(_frameBuffer[6]) << 8) | _frameBuffer[7];
    _data.pm10_standard  = (static_cast<uint16_t>(_frameBuffer[8]) << 8) | _frameBuffer[9];

    // Bytes 10-15: Atmospheric environment (Real-world air)
    _data.pm1_0_env = (static_cast<uint16_t>(_frameBuffer[10]) << 8) | _frameBuffer[11];
    _data.pm2_5_env = (static_cast<uint16_t>(_frameBuffer[12]) << 8) | _frameBuffer[13];
    _data.pm10_env  = (static_cast<uint16_t>(_frameBuffer[14]) << 8) | _frameBuffer[15];

    // Bytes 16-27: Particle counts per 0.1 Liter
    _data.particles_0_3um = (static_cast<uint16_t>(_frameBuffer[16]) << 8) | _frameBuffer[17];
    _data.particles_0_5um = (static_cast<uint16_t>(_frameBuffer[18]) << 8) | _frameBuffer[19];
    _data.particles_1_0um = (static_cast<uint16_t>(_frameBuffer[20]) << 8) | _frameBuffer[21];
    _data.particles_2_5um = (static_cast<uint16_t>(_frameBuffer[22]) << 8) | _frameBuffer[23];
    _data.particles_5_0um = (static_cast<uint16_t>(_frameBuffer[24]) << 8) | _frameBuffer[25];
    _data.particles_10um  = (static_cast<uint16_t>(_frameBuffer[26]) << 8) | _frameBuffer[27];

    _data.isValid = true;
    _data.lastReadMs = millis();
}

const PMData& PMSensor::getData() const {
    return _data;
}

bool PMSensor::isHealthy() const {
    return _data.isValid && (millis() - _data.lastReadMs <= PMS_READ_TIMEOUT_MS);
}
