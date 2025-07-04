import time
import board
import busio
from adafruit_ina219 import INA219
from adafruit_ahtx0 import AHTx0
from RPLCD.i2c import CharLCD

# Configuration Constants
PAGE_DELAY = 5          # Display page rotation interval (seconds)
SHUNT_RESISTANCE = 0.1  # INA219 shunt resistance (ohms)
VOLTAGE_HEALTHY = 11.5  # Healthy battery threshold (V)
VOLTAGE_MODERATE = 10.5 # Moderate battery threshold (V)
MAX_VOLTAGE = 12.6      # Fully charged battery voltage (V)
MIN_VOLTAGE = 9.0       # Fully discharged battery voltage (V)

# Initialize I2C bus and sensors
i2c = busio.I2C(board.SCL, board.SDA)
ina219 = INA219(i2c)
aht25 = AHTx0(i2c)
lcd = CharLCD('PCF8574', 0x27, cols=16, rows=2)

def get_battery_status(voltage):
    """Determine battery health status based on voltage"""
    if voltage >= VOLTAGE_HEALTHY:
        return "Healthy"
    elif voltage >= VOLTAGE_MODERATE:
        return "Moderate"
    else:
        return "Critical"

# Main monitoring loop
page = 0
print("Battery monitoring system started...")

try:
    while True:
        # Read sensor data
        bus_v = ina219.bus_voltage
        current_a = ina219.current / 1000.0  # Convert mA to A
        impedance = (bus_v / current_a) if current_a > 0.0001 else 0.0
        soc = max(0, min(100, (bus_v - MIN_VOLTAGE)/(MAX_VOLTAGE-MIN_VOLTAGE)*100))
        dod = 100 - soc
        temp = aht25.temperature
        hum = aht25.relative_humidity
        status = get_battery_status(bus_v)

        # Update LCD display
        lcd.clear()
        if page == 0:
            lcd.write_string(f'Battery:{status:<7}')
            lcd.crlf()
            lcd.write_string(f'V:{bus_v:.2f} I:{ina219.current:.0f}mA')
        elif page == 1:
            lcd.write_string(f'Battery:{status:<7}')
            lcd.crlf()
            lcd.write_string(f'T:{temp:.1f} H:{hum:.0f}%')
        elif page == 2:
            lcd.write_string('SVM:OFF')
            lcd.crlf()
            lcd.write_string(f'SOC:{int(soc)}% SOH:OFF')
        elif page == 3:
            lcd.write_string('SVM:OFF')
            lcd.crlf()
            lcd.write_string(f'DOD:{int(dod)}% Z:{impedance:.1f}R')

        page = (page + 1) % 4
        time.sleep(PAGE_DELAY)

except KeyboardInterrupt:
    lcd.clear()
    lcd.write_string("System Stopped")
    print("Battery monitoring stopped by user")
except Exception as e:
    lcd.clear()
    lcd.write_string("Error Occurred")
    print(f"Error: {e}")
