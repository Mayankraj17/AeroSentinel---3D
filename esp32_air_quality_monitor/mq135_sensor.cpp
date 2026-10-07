#include "mq135_sensor.h"
#include "config.h"
#include <math.h>

MQ135Sensor::MQ135Sensor()
    : _pin(MQ135_ANALOG_PIN),
      _rlKohm(MQ135_RL_KOHM),
      _roKohm(MQ135_RO_CLEAN_AIR_KOHM) {}

void MQ135Sensor::begin(int pin, float rlKohm, float roCleanAirKohm) {
    _pin = pin;
    _rlKohm = rlKohm;
    _roKohm = roCleanAirKohm;

    pinMode(_pin, INPUT);

    // Configure ESP32 ADC for full 0 to ~3.3V range with 12-bit resolution
    analogReadResolution(12);
#if defined(ESP32)
    analogSetPinAttenuation(_pin, ADC_11db);
#endif
}

uint32_t MQ135Sensor::readOversampledAdc() {
    uint32_t sum = 0;
    for (int i = 0; i < MQ135_ADC_SAMPLES; ++i) {
        sum += analogRead(_pin);
        delayMicroseconds(200);
    }
    return sum / MQ135_ADC_SAMPLES;
}

uint32_t MQ135Sensor::readOversampledMilliVolts() {
    uint32_t sum = 0;
    for (int i = 0; i < MQ135_ADC_SAMPLES; ++i) {
#if defined(ESP32)
        // Uses ESP32 factory eFuse calibration table for improved ADC linearity
        sum += analogReadMilliVolts(_pin);
#else
        sum += (analogRead(_pin) * 3300) / 4095;
#endif
        delayMicroseconds(200);
    }
    return sum / MQ135_ADC_SAMPLES;
}

void MQ135Sensor::read(MQ135Data& outData) {
    outData.rawAdc = readOversampledAdc();
    outData.voltageMv = readOversampledMilliVolts();

    // Convert millivolts to volts
    float vOut = outData.voltageMv / 1000.0f;

    // Safety checks against division-by-zero or out-of-range voltages
    if (vOut <= 0.02f) {
        outData.rsKohm = 999.0f;
        outData.rsRoRatio = 999.0f;
        outData.ppmCO2Equiv = 0.0f;
        outData.airQuality = "Sensor Open / Disconnected";
        outData.isValid = false;
        return;
    }

    // Circuit model: Sensor resistance Rs in series with load resistance RL
    // Vout = Vsupply * (RL / (Rs + RL))  =>  Rs = RL * ((Vsupply - Vout) / Vout)
    float vSupply = MQ135_VCC_SUPPLY;
    if (vOut >= vSupply) {
        vOut = vSupply - 0.05f;
    }

    outData.rsKohm = _rlKohm * ((vSupply - vOut) / vOut);
    outData.rsRoRatio = (_roKohm > 0.0f) ? (outData.rsKohm / _roKohm) : 1.0f;

    // PPM CO2-equivalent exponential curve
    if (outData.rsRoRatio > 0.0f) {
        outData.ppmCO2Equiv = MQ135_PARAM_A * pow(outData.rsRoRatio, MQ135_PARAM_B);
    } else {
        outData.ppmCO2Equiv = 0.0f;
    }

    outData.airQuality = classifyAirQuality(outData.ppmCO2Equiv);
    outData.isValid = true;
}

const char* MQ135Sensor::classifyAirQuality(float ppm) {
    if (ppm <= 450.0f) {
        return "Excellent (Clean Outdoor Air)";
    } else if (ppm <= 800.0f) {
        return "Good (Normal Indoor Air)";
    } else if (ppm <= 1000.0f) {
        return "Moderate (Fair Ventilation)";
    } else if (ppm <= 1500.0f) {
        return "Poor (Heavy Air / Stale)";
    } else {
        return "Hazardous (Ventilation Required)";
    }
}

float MQ135Sensor::calibrateR0InCleanAir(int samples, uint32_t delayBetweenSamplesMs) {
    float rsSum = 0.0f;
    int validCount = 0;

    for (int i = 0; i < samples; ++i) {
        MQ135Data d;
        read(d);
        if (d.isValid && d.rsKohm > 0.0f) {
            rsSum += d.rsKohm;
            validCount++;
        }
        delay(delayBetweenSamplesMs);
    }

    if (validCount == 0) return _roKohm;

    float avgRs = rsSum / validCount;
    // For standard clean air (~415 ppm CO2 baseline):
    // Rs / R0 = (ppm / A) ^ (1 / B)
    // R0 = Rs / ((415.0 / A) ^ (1 / B))
    float cleanRatio = pow(415.0f / MQ135_PARAM_A, 1.0f / MQ135_PARAM_B);
    _roKohm = avgRs / cleanRatio;
    return _roKohm;
}

void MQ135Sensor::setR0(float r0Kohm) {
    if (r0Kohm > 0.0f) {
        _roKohm = r0Kohm;
    }
}

float MQ135Sensor::getR0() const {
    return _roKohm;
}
