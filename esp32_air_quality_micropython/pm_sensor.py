import time
from machine import UART, Pin

class PMSensor:
    FRAME_LEN = 32
    START_1 = 0x42
    START_2 = 0x4D

    def __init__(self, uart_id=2, rx_pin=16, tx_pin=17, baudrate=9600, timeout_ms=3000):
        self.uart = UART(uart_id, baudrate=baudrate, rx=Pin(rx_pin), tx=Pin(tx_pin), timeout=10)
        self.timeout_ms = timeout_ms
        self.buffer = bytearray()
        self.last_read_ms = 0
        self.is_valid = False
        self.latest_data = {
            "pm1_0_standard": 0,
            "pm2_5_standard": 0,
            "pm10_standard": 0,
            "pm1_0_env": 0,
            "pm2_5_env": 0,
            "pm10_env": 0,
            "particles_0_3um": 0,
            "particles_0_5um": 0,
            "particles_1_0um": 0,
            "particles_2_5um": 0,
            "particles_5_0um": 0,
            "particles_10um": 0,
            "sensor_valid": False
        }

    def update(self):
        """Non-blocking UART buffer reading and frame parser."""
        if self.uart.any():
            chunk = self.uart.read()
            if chunk:
                self.buffer.extend(chunk)

        # Look for the start marker (0x42, 0x4D)
        while len(self.buffer) >= self.FRAME_LEN:
            if self.buffer[0] != self.START_1 or self.buffer[1] != self.START_2:
                # Slide buffer window forward until header is found
                del self.buffer[0]
                continue

            # Complete candidate frame found
            frame = self.buffer[:self.FRAME_LEN]
            del self.buffer[:self.FRAME_LEN]

            if self._verify_checksum(frame):
                self._parse_frame(frame)
                return

        # Check for timeout if no valid frame recently received
        if self.is_valid and time.ticks_diff(time.ticks_ms(), self.last_read_ms) > self.timeout_ms:
            self.is_valid = False
            self.latest_data["sensor_valid"] = False

    def _verify_checksum(self, frame):
        computed = sum(frame[:30]) & 0xFFFF
        expected = (frame[30] << 8) | frame[31]
        return computed == expected

    def _parse_frame(self, frame):
        # Unpack big-endian unsigned 16-bit integers
        self.latest_data = {
            "pm1_0_standard": (frame[4] << 8) | frame[5],
            "pm2_5_standard": (frame[6] << 8) | frame[7],
            "pm10_standard":  (frame[8] << 8) | frame[9],
            "pm1_0_env":      (frame[10] << 8) | frame[11],
            "pm2_5_env":      (frame[12] << 8) | frame[13],
            "pm10_env":       (frame[14] << 8) | frame[15],
            "particles_0_3um": (frame[16] << 8) | frame[17],
            "particles_0_5um": (frame[18] << 8) | frame[19],
            "particles_1_0um": (frame[20] << 8) | frame[21],
            "particles_2_5um": (frame[22] << 8) | frame[23],
            "particles_5_0um": (frame[24] << 8) | frame[25],
            "particles_10um":  (frame[26] << 8) | frame[27],
            "sensor_valid":   True
        }
        self.is_valid = True
        self.last_read_ms = time.ticks_ms()

    def get_data(self):
        return self.latest_data

    def is_healthy(self):
        return self.is_valid and (time.ticks_diff(time.ticks_ms(), self.last_read_ms) <= self.timeout_ms)
