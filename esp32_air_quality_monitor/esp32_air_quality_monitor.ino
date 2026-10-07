/**
 * ============================================================================
 * ESP32 Air Quality Monitor (Production-Ready Architecture)
 * ============================================================================
 * Hardware:
 *   - ESP32 Development Board (ESP32-WROOM-32)
 *   - Plantower PMS5003 / PMS7003 (UART / Serial2)
 *   - MQ-135 Hazardous Gas & Air Quality Sensor (ADC1 GPIO 34)
 *
 * Features:
 *   - Non-blocking UART parser with 16-bit frame checksum validation
 *   - Noise-filtered 12-bit ADC sampling with eFuse voltage compensation
 *   - Background non-blocking Wi-Fi management with auto-reconnection
 *   - Native SNTP time synchronization for ISO-8601 & Epoch timestamps
 *   - Structured ArduinoJson payload generation
 *   - MQTT-ready publish dispatch hook
 * ============================================================================
 */

#include <Arduino.h>
#include "config.h"
#include "pm_sensor.h"
#include "mq135_sensor.h"
#include "time_sync.h"
#include "wifi_manager.h"
#include "payload_builder.h"

// System Components
PMSensor       pmSensor;
MQ135Sensor    mq135Sensor;
TimeSync       timeSync;
WiFiManager    wifiManager;
PayloadBuilder payloadBuilder;

// Runtime state
uint32_t lastPublishTimeMs = 0;

// Forward declaration for MQTT dispatch hook
void handleMqttTransmission(const String& jsonPayload);

void setup() {
    // 1. Initialize Serial Monitor
    Serial.begin(SERIAL_MONITOR_BAUD);
    delay(1000); // Allow hardware USB CDC to settle

    Serial.println("\n=======================================================");
    Serial.println("  ESP32 AIR QUALITY MONITOR - PRODUCTION FIRMWARE");
    Serial.println("=======================================================");

    // 2. Initialize PM Sensor (UART2 on GPIO 16 RX, GPIO 17 TX)
    Serial.printf("[Init] Initializing PMS5003/7003 on UART2 (RX: %d, TX: %d, Baud: %d)...\n",
                  PMS_RX_PIN, PMS_TX_PIN, PMS_BAUD_RATE);
    pmSensor.begin(PMS_RX_PIN, PMS_TX_PIN, PMS_BAUD_RATE);

    // 3. Initialize MQ-135 Gas Sensor (ADC1 Pin 34)
    Serial.printf("[Init] Initializing MQ-135 on ADC GPIO %d (RL: %.1fk, R0: %.1fk)...\n",
                  MQ135_ANALOG_PIN, MQ135_RL_KOHM, MQ135_RO_CLEAN_AIR_KOHM);
    mq135Sensor.begin(MQ135_ANALOG_PIN, MQ135_RL_KOHM, MQ135_RO_CLEAN_AIR_KOHM);

    // 4. Initialize Wi-Fi Manager (Non-blocking)
    Serial.println("[Init] Initializing Wi-Fi Manager...");
    wifiManager.begin(WIFI_SSID, WIFI_PASSWORD);

    // 5. Initialize SNTP Time Sync
    Serial.printf("[Init] Initializing SNTP Time Sync (Server: %s)...\n", NTP_SERVER_PRIMARY);
    timeSync.begin(GMT_OFFSET_SEC, DAYLIGHT_OFFSET_SEC, NTP_SERVER_PRIMARY, NTP_SERVER_SECONDARY);

    Serial.println("[Init] Initialization complete. Entering measurement loop.\n");
}

void loop() {
    // 1. Update background services continuously
    wifiManager.update();
    pmSensor.update();

    // 2. Non-blocking periodic measurement and telemetry cycle
    uint32_t currentMillis = millis();
    if (currentMillis - lastPublishTimeMs >= SENSOR_READ_INTERVAL_MS) {
        lastPublishTimeMs = currentMillis;

        // Sample MQ-135 Gas Sensor
        MQ135Data gasData;
        mq135Sensor.read(gasData);

        // Retrieve latest cached Particulate Matter data
        const PMData& pmData = pmSensor.getData();

        // Generate JSON formatted for human readability on Serial Monitor
        String prettyJson = payloadBuilder.buildJson(pmData, gasData, timeSync, wifiManager, true);

        // Generate compact minified JSON payload for transmission
        String compactJson = payloadBuilder.buildJson(pmData, gasData, timeSync, wifiManager, false);

        // Output to Serial Monitor
        Serial.println("\n--- [TELEMETRY PAYLOAD] -------------------------------");
        Serial.println(prettyJson);
        Serial.println("-------------------------------------------------------");

        // Transmit via MQTT if connected
        handleMqttTransmission(compactJson);
    }
}

/**
 * Hook for MQTT Transmission.
 * Plug your preferred MQTT client (e.g. PubSubClient) directly into this routine.
 */
void handleMqttTransmission(const String& jsonPayload) {
    if (!wifiManager.isConnected()) {
        // Serial.println("[MQTT] Skipped: Wi-Fi not connected.");
        return;
    }

    if (!MQTT_ENABLED) {
        // Ready for MQTT: Provide visual confirmation that payload is prepared for transmission
        Serial.printf("[MQTT Hook] Ready to publish (%u bytes) to topic '%s'\n",
                      jsonPayload.length(), MQTT_TOPIC_TELEMETRY);
        return;
    }

    /*
     * EXAMPLE PUBSUBCLIENT INTEGRATION:
     * -----------------------------------------------------------------------
     * #include <PubSubClient.h>
     * WiFiClient espClient;
     * PubSubClient mqttClient(espClient);
     *
     * In setup():
     *   mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
     *
     * In loop() or here:
     *   if (!mqttClient.connected()) {
     *       mqttClient.connect(wifiManager.getDeviceId().c_str(), MQTT_CLIENT_USER, MQTT_CLIENT_PASS);
     *   }
     *   mqttClient.publish(MQTT_TOPIC_TELEMETRY, jsonPayload.c_str());
     * -----------------------------------------------------------------------
     */
}
