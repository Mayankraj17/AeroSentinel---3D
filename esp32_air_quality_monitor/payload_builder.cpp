#include "payload_builder.h"
#include "config.h"

PayloadBuilder::PayloadBuilder() {}

String PayloadBuilder::buildJson(const PMData& pmData,
                                 const MQ135Data& gasData,
                                 const TimeSync& timeSync,
                                 const WiFiManager& wifi,
                                 bool prettyPrint) {
#if ARDUINOJSON_VERSION_MAJOR >= 7
    JsonDocument doc;
#else
    StaticJsonDocument<1024> doc;
#endif

    // 1. Device & Time Metadata
    doc["device_id"]  = wifi.getDeviceId();
    
    char isoTimestamp[32];
    timeSync.getIso8601(isoTimestamp, sizeof(isoTimestamp));
    doc["timestamp"]  = isoTimestamp;
    doc["time_synced"] = timeSync.isSynced();
    doc["epoch"]      = static_cast<uint32_t>(timeSync.getEpochTime());
    doc["uptime_sec"] = timeSync.getUptimeSeconds();

    // 2. Wi-Fi Status
    JsonObject wifiObj = doc["wifi"].to<JsonObject>();
    wifiObj["connected"] = wifi.isConnected();
    if (wifi.isConnected()) {
        wifiObj["rssi_dbm"] = wifi.getRSSI();
        wifiObj["ip"]       = wifi.getIpAddress();
    } else {
        wifiObj["rssi_dbm"] = nullptr;
        wifiObj["ip"]       = nullptr;
    }

    // 3. Particulate Matter (PMS5003 / PMS7003)
    JsonObject pmObj = doc["particulate_matter"].to<JsonObject>();
    pmObj["sensor_valid"] = pmData.isValid;
    if (pmData.isValid) {
        // Atmospheric environmental concentrations (ug/m3)
        pmObj["pm1_0_ug_m3"]   = pmData.pm1_0_env;
        pmObj["pm2_5_ug_m3"]   = pmData.pm2_5_env;
        pmObj["pm10_ug_m3"]    = pmData.pm10_env;
        
        // Factory standard calibration (CF=1)
        pmObj["pm2_5_cf1"]     = pmData.pm2_5_standard;
        
        // Particle counts per 0.1L air
        JsonObject countObj    = pmObj["particle_counts_0_1L"].to<JsonObject>();
        countObj["gt_0_3um"]   = pmData.particles_0_3um;
        countObj["gt_0_5um"]   = pmData.particles_0_5um;
        countObj["gt_2_5um"]   = pmData.particles_2_5um;
    } else {
        pmObj["status"] = "Sensor Offline / Waiting for Data";
    }

    // 4. Gas Concentration (MQ-135)
    JsonObject gasObj = doc["gas_mq135"].to<JsonObject>();
    gasObj["sensor_valid"] = gasData.isValid;
    gasObj["raw_adc"]      = gasData.rawAdc;
    gasObj["voltage_mv"]   = gasData.voltageMv;

    if (gasData.isValid) {
        gasObj["rs_kohm"]       = serialized(String(gasData.rsKohm, 2));
        gasObj["rs_ro_ratio"]   = serialized(String(gasData.rsRoRatio, 3));
        gasObj["ppm_co2_equiv"] = serialized(String(gasData.ppmCO2Equiv, 1));
        gasObj["air_quality"]   = gasData.airQuality;
    } else {
        gasObj["air_quality"]   = gasData.airQuality;
    }

    // Serialize to String
    String output;
    if (prettyPrint) {
        serializeJsonPretty(doc, output);
    } else {
        serializeJson(doc, output);
    }

    return output;
}
