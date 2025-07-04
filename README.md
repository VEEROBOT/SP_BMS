# Battery Monitoring System using Raspberry Pi

## Overview

This project implements a real-time battery monitoring system using a Raspberry Pi. It continuously monitors crucial battery parameters and displays them on a 16x2 I2C LCD screen. The system operates in headless mode and runs automatically as a systemd service at startup, making it perfect for standalone deployment.

## Features

- **Real-time monitoring** of voltage, current, impedance, SOC (State of Charge), DOD (Depth of Discharge), temperature, and humidity
- **Intelligent battery health classification** based on voltage thresholds
- **Multi-page LCD display** rotating every 5 seconds:
  - **Page 1**: Battery status (Healthy/Moderate/Critical), voltage, current
  - **Page 2**: Battery status, temperature, humidity  
  - **Page 3**: SVM status (placeholder), SOC, SOH status (placeholder for future ML integration)
  - **Page 4**: SVM status (placeholder), DOD, battery impedance
- **Fully headless operation** - no display, keyboard, or network required
- **Auto-start capability** via systemd service
- **Isolated Python environment** using virtual environment for clean dependency management

## Hardware Requirements

| Component | Model/Type | I2C Address | Purpose |
|-----------|------------|-------------|---------|
| Microcontroller | Raspberry Pi 4 (recommended) | - | Main controller |
| Voltage/Current Sensor | INA219 | 0x40 | Battery voltage and current measurement |
| Environmental Sensor | AHT25/AHT20/AHT21 | 0x38 | Temperature and humidity monitoring |
| Display | 16x2 LCD with I2C backpack (PCF8574) | 0x27 | Real-time data visualization |

### Wiring Connections

```
Raspberry Pi GPIO:
- Pin 3 (GPIO2) → SDA (all I2C devices)
- Pin 5 (GPIO3) → SCL (all I2C devices)  
- Pin 6 (GND) → GND (all devices)
- Pin 1 (3.3V) → VCC (sensors)
- Pin 2 (5V) → VCC (LCD - if required)
```

## Battery Health Classification

The system uses voltage-based thresholds for battery health assessment:

| Status | Voltage Range | Description |
|--------|---------------|-------------|
| **Healthy** | ≥ 11.5V | Battery in good condition |
| **Moderate** | 10.5V - 11.4V | Battery showing signs of degradation |
| **Critical** | < 10.5V | Battery requires immediate attention |

## Installation Guide

### 1. Raspberry Pi OS Setup

```bash
# Enable I2C interface
sudo raspi-config
# Navigate to: Interface Options → I2C → Enable → Finish
sudo reboot
```

### 2. System Updates and Dependencies

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install python3-pip python3-smbus i2c-tools python3-venv git -y
```

### 3. Verify I2C Devices

```bash
# Check if I2C devices are detected
i2cdetect -y 1

# Expected output should show devices at 0x27, 0x38, and 0x40
```

### 4. Project Setup

```bash
# Create project directory
mkdir -p ~/battery-monitor
cd ~/battery-monitor

# Create and activate Python virtual environment
python3 -m venv batteryenv
source batteryenv/bin/activate

# Install required Python libraries
pip install adafruit-circuitpython-ina219 adafruit-circuitpython-ahtx0 RPLCD adafruit-blinka
```

### 5. Create the Python Script

Save the following as `battery_monitor.py` in the `~/battery-monitor` directory:

```python
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
```

### 6. Test the Script

```bash
# Activate virtual environment
source ~/battery-monitor/batteryenv/bin/activate

# Run the script manually to test
python battery_monitor.py

# Press Ctrl+C to stop
```

### 7. Create Systemd Service for Auto-Start

```bash
sudo nano /etc/systemd/system/battery_monitor.service
```

Add the following content:

```ini
[Unit]
Description=Battery Monitoring System
After=multi-user.target
Wants=multi-user.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/home/pi/battery-monitor
Environment=PATH=/home/pi/battery-monitor/batteryenv/bin
ExecStart=/home/pi/battery-monitor/batteryenv/bin/python /home/pi/battery-monitor/battery_monitor.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 8. Enable and Start the Service

```bash
# Reload systemd configuration
sudo systemctl daemon-reload

# Enable service to start at boot
sudo systemctl enable battery_monitor.service

# Start the service immediately
sudo systemctl start battery_monitor.service

# Check service status
sudo systemctl status battery_monitor.service
```

## System Management Commands

| Operation | Command |
|-----------|---------|
| **Check service status** | `sudo systemctl status battery_monitor.service` |
| **View real-time logs** | `sudo journalctl -u battery_monitor.service -f` |
| **View recent logs** | `sudo journalctl -u battery_monitor.service -n 50 --no-pager` |
| **Stop service** | `sudo systemctl stop battery_monitor.service` |
| **Start service** | `sudo systemctl start battery_monitor.service` |
| **Restart service** | `sudo systemctl restart battery_monitor.service` |
| **Disable auto-start** | `sudo systemctl disable battery_monitor.service` |

## Troubleshooting

### Common Issues and Solutions

**Issue**: Service fails to start
```bash
# Check detailed error logs
sudo journalctl -u battery_monitor.service -n 20

# Verify I2C devices are connected
i2cdetect -y 1

# Test script manually
cd ~/battery-monitor
source batteryenv/bin/activate
python battery_monitor.py
```

**Issue**: I2C devices not detected
```bash
# Check I2C is enabled
sudo raspi-config
# Interface Options → I2C → Enable

# Check physical connections
# Verify VCC, GND, SDA, SCL connections
```

**Issue**: Permission errors
```bash
# Add user to i2c group
sudo usermod -a -G i2c pi
sudo reboot
```

## Technical Specifications

### Measurement Ranges
- **Voltage**: 0-26V (INA219 range)
- **Current**: ±3.2A (with 0.1Ω shunt)
- **Temperature**: -40°C to +85°C (AHT25)
- **Humidity**: 0-100% RH (AHT25)

### Update Intervals
- **Sensor readings**: Every 5 seconds
- **Display refresh**: Every 5 seconds (page rotation)
- **LCD clear/write**: Optimized to minimize flicker

## Future Enhancements

- [ ] Integration of SVM (Support Vector Machine) for advanced battery health classification
- [ ] Enhanced SOH (State of Health) calculation algorithms
- [ ] Data logging to SD card with CSV export
- [ ] Web interface for remote monitoring
- [ ] Alert system for critical battery conditions
- [ ] Historical data visualization
- [ ] Battery cycle counting
- [ ] Temperature-compensated SOC calculations

## Project Structure

```
~/battery-monitor/
├── battery_monitor.py          # Main monitoring script
├── batteryenv/                 # Python virtual environment
│   ├── bin/
│   ├── lib/
│   └── ...
└── README.md                   # This documentation
```

## License

This project is developed for educational purposes. Feel free to modify and adapt for your specific requirements.

## Support

For issues related to:
- **Hardware connections**: Check wiring diagrams and I2C device detection
- **Software errors**: Review systemd logs and test manual script execution
- **Performance optimization**: Consider measurement intervals and display refresh rates

---

**Note**: This system is designed for educational and prototyping purposes. For production battery monitoring applications, consider additional safety measures and calibration procedures.
