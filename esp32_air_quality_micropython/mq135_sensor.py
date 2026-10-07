import time
from machine import ADC, Pin

class MQ135Sensor:
    def __init__(self, pin=34, rl_kohm=10.0, ro_clean_air_kohm=76.63, 
                 vcc_supply=5.0, vref_esp32=3.3, samples=32,
                 param_a=116.6020682, param_b=-2.769034857):
        self.adc = ADC(Pin(pin))
        # Configure full-scale 3.3V attenuation
        self.adc.atten(ADC.ATTN_11DB)
        
        # In modern MicroPython, width is 12-bit by default (0-4095)
        if hasattr(self.adc, 'width'):
            self.adc.width(ADC.WIDTH_12BIT)

        self.rl_kohm = rl_kohm
        self.ro_kohm = ro_clean_air_kohm
        self.vcc_supply = vcc_supply
        self.vref_esp32 = vref_esp32
        self.samples = samples
        self.param_a = param_a
        self.param_b = param_b

    def _read_raw_oversampled(self):
        total = 0
        for _ in range(self.samples):
            # adc.read() returns 12-bit 0-4095
            total += self.adc.read()
            time.sleep_us(200)
        return total // self.samples

    def _read_millivolts(self, raw_adc):
        # Check if native calibrated read_uv is available in this MicroPython build
        if hasattr(self.adc, 'read_uv'):
            try:
                total_uv = 0
                for _ in range(self.samples):
                    total_uv += self.adc.read_uv()
                    time.sleep_us(200)
                return (total_uv // self.samples) // 1000
            except Exception:
                pass
        # Fallback to direct calculation
        return int((raw_adc * (self.vref_esp32 * 1000)) / 4095)

    def read(self):
        raw_adc = self._read_raw_oversampled()
        voltage_mv = self._read_millivolts(raw_adc)
        v_out = voltage_mv / 1000.0

        if v_out <= 0.02:
            return {
                "sensor_valid": False,
                "raw_adc": raw_adc,
                "voltage_mv": voltage_mv,
                "rs_kohm": 999.0,
                "rs_ro_ratio": 999.0,
                "ppm_co2_equiv": 0.0,
                "air_quality": "Sensor Open / Disconnected"
            }

        if v_out >= self.vcc_supply:
            v_out = self.vcc_supply - 0.05

        # Rs = RL * (Vsupply - Vout) / Vout
        rs_kohm = self.rl_kohm * ((self.vcc_supply - v_out) / v_out)
        ratio = rs_kohm / self.ro_kohm if self.ro_kohm > 0 else 1.0

        # Estimated CO2 equivalent PPM
        if ratio > 0:
            ppm = self.param_a * (ratio ** self.param_b)
        else:
            ppm = 0.0

        return {
            "sensor_valid": True,
            "raw_adc": raw_adc,
            "voltage_mv": voltage_mv,
            "rs_kohm": round(rs_kohm, 2),
            "rs_ro_ratio": round(ratio, 3),
            "ppm_co2_equiv": round(ppm, 1),
            "air_quality": self._classify_air_quality(ppm)
        }

    def _classify_air_quality(self, ppm):
        if ppm <= 450.0:
            return "Excellent (Clean Outdoor Air)"
        elif ppm <= 800.0:
            return "Good (Normal Indoor Air)"
        elif ppm <= 1000.0:
            return "Moderate (Fair Ventilation)"
        elif ppm <= 1500.0:
            return "Poor (Heavy Air / Stale)"
        else:
            return "Hazardous (Ventilation Required)"

    def calibrate_r0(self, samples=50, delay_ms=100):
        """Calibrates R0 in fresh clean outdoor air (baseline ~415 ppm CO2)."""
        rs_readings = []
        for _ in range(samples):
            data = self.read()
            if data["sensor_valid"] and data["rs_kohm"] > 0:
                rs_readings.append(data["rs_kohm"])
            time.sleep_ms(delay_ms)

        if not rs_readings:
            return self.ro_kohm

        avg_rs = sum(rs_readings) / len(rs_readings)
        # R0 = Rs / ((415 / A) ^ (1 / B))
        clean_ratio = (415.0 / self.param_a) ** (1.0 / self.param_b)
        self.ro_kohm = avg_rs / clean_ratio
        return round(self.ro_kohm, 2)
