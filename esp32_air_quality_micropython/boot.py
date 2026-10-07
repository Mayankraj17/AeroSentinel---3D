# boot.py - Executes once on ESP32 cold boot
import esp
import gc

# Disable low-level OS debug chatter on UART0
esp.osdebug(None)

# Run initial garbage collection
gc.enable()
gc.collect()
