#include "time_sync.h"

TimeSync::TimeSync() {}

void TimeSync::begin(long gmtOffsetSec, int daylightOffsetSec, const char* ntp1, const char* ntp2) {
    // Configure ESP32 native SNTP
    configTime(gmtOffsetSec, daylightOffsetSec, ntp1, ntp2);
}

bool TimeSync::isSynced() const {
    time_t now = 0;
    time(&now);
    // Any timestamp past Jan 1, 2024 (1704067200) indicates valid synchronization
    return (now > 1704067200);
}

time_t TimeSync::getEpochTime() const {
    time_t now = 0;
    time(&now);
    return now;
}

void TimeSync::getIso8601(char* buffer, size_t maxLen) const {
    if (!buffer || maxLen == 0) return;

    if (isSynced()) {
        time_t now = getEpochTime();
        struct tm timeinfo;
        gmtime_r(&now, &timeinfo);
        // Format ISO-8601 UTC: YYYY-MM-DDTHH:MM:SSZ
        strftime(buffer, maxLen, "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
    } else {
        // Fallback representation with uptime
        snprintf(buffer, maxLen, "BOOT+%lus", static_cast<unsigned long>(getUptimeSeconds()));
    }
}

uint32_t TimeSync::getUptimeSeconds() const {
    return millis() / 1000;
}
