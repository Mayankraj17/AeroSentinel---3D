import time

class TimeSync:
    UNIX_EPOCH_OFFSET = 946684800  # Seconds between 1970-01-01 and MicroPython epoch 2000-01-01

    def __init__(self, ntp_host="pool.ntp.org", gmt_offset_hours=0):
        self.ntp_host = ntp_host
        self.gmt_offset_hours = gmt_offset_hours
        self.is_synced = False
        self.boot_ticks_ms = time.ticks_ms()

    def sync(self):
        """Attempts to synchronize internal RTC via NTP. Returns True on success."""
        try:
            import ntptime
            ntptime.host = self.ntp_host
            ntptime.settime()
            self.is_synced = True
            print(f"[NTP] Clock synchronized successfully via {self.ntp_host}")
            return True
        except Exception as e:
            # print(f"[NTP] Sync failed: {e}")
            return False

    def get_epoch(self):
        """Returns standard Unix epoch (seconds since 1970-01-01). 0 if not synced."""
        if self.is_synced:
            return time.time() + self.UNIX_EPOCH_OFFSET
        return 0

    def get_uptime_sec(self):
        return time.ticks_diff(time.ticks_ms(), self.boot_ticks_ms) // 1000

    def get_iso8601_timestamp(self):
        """Returns ISO-8601 formatted string e.g. 2026-10-06T12:45:30Z."""
        if self.is_synced:
            # time.gmtime() returns (year, month, mday, hour, minute, second, weekday, yearday)
            t = time.gmtime()
            return f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}Z"
        else:
            return f"BOOT+{self.get_uptime_sec()}s"
