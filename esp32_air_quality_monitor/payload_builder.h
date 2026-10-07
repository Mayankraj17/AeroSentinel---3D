#pragma once

#include <Arduino.h>
#include <ArduinoJson.h>
#include "pm_sensor.h"
#include "mq135_sensor.h"
#include "time_sync.h"
#include "wifi_manager.h"

class PayloadBuilder {
public:
    PayloadBuilder();

    // Construct the complete JSON document into output string
    // prettyPrint = true formats with indentation for readable Serial monitor debugging
    // prettyPrint = false formats compact minified JSON for efficient MQTT transmission
    String buildJson(const PMData& pmData,
                     const MQ135Data& gasData,
                     const TimeSync& timeSync,
                     const WiFiManager& wifi,
                     bool prettyPrint = false);
};
