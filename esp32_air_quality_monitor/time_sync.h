#pragma once

#include <Arduino.h>
#include <time.h>

class TimeSync {
public:
    TimeSync();

    // Initialize SNTP with servers and offsets
    void begin(long gmtOffsetSec = 0, int daylightOffsetSec = 0,
               const char* ntp1 = "pool.ntp.org",
               const char* ntp2 = "time.nist.gov");

    // Check whether the real-time clock has synced with NTP
    bool isSynced() const;

    // Retrieve current UTC Unix epoch timestamp (0 if not synced)
    time_t getEpochTime() const;

    // Format current time into ISO-8601 string (e.g., "2026-10-06T12:45:30Z")
    // Falls back to "BOOT+<seconds>s" if NTP has not yet synchronized.
    void getIso8601(char* buffer, size_t maxLen) const;

    // Get device uptime in seconds
    uint32_t getUptimeSeconds() const;
};
