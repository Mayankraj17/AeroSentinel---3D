#pragma once

#include <Arduino.h>

struct MQ135Data {
    uint16_t rawAdc;          // Raw 12-bit ADC value (0-4095)
    uint16_t voltageMv;       // Measured voltage in millivolts
    float    rsKohm;          // Current sensor resistance (kOhms)
    float    rsRoRatio;       // Rs / R0 ratio
    float    ppmCO2Equiv;     // Estimated CO2-equivalent concentration in PPM
    const char* airQuality;   // Qualitative classification ("Good", "Moderate", etc.)
    bool     isValid;         // Reading integrity flag
};

class MQ135Sensor {
public:
    MQ135Sensor();

    // Initialize ADC settings and pin
    void begin(int pin, float rlKohm = 10.0f, float roCleanAirKohm = 76.63f);

    // Perform oversampled ADC reading and recalculate metrics
    void read(MQ135Data& outData);

    // Utility: Calibrate R0 in fresh/clean outdoor air (baseline ~415 ppm CO2)
    float calibrateR0InCleanAir(int samples = 50, uint32_t delayBetweenSamplesMs = 100);

    // Update calibrated R0 at runtime
    void setR0(float r0Kohm);
    float getR0() const;

private:
    int   _pin;
    float _rlKohm;
    float _roKohm;

    uint32_t readOversampledAdc();
    uint32_t readOversampledMilliVolts();
    const char* classifyAirQuality(float ppm);
};
