Battery Monitoring System using Raspberry Pi

Overview

This project implements a battery monitoring system using a Raspberry Pi. It monitors key battery parameters in real-time and displays them on a 16x2 I2C LCD screen. The system works in headless mode and runs automatically as a systemd service at startup.

Features

Monitors voltage, current, impedance, SOC (State of Charge), DOD (Depth of Discharge), temperature, and humidity.

Displays information in 4 pages rotating every 5 seconds:

Page 1: Battery status (Healthy/Moderate/Critical), voltage, current.

Page 2: Battery status, temperature, humidity.

Page 3: SVM:OFF, SOC, SOH:OFF (placeholder for future SVM integration).

Page 4: SVM:OFF, DOD, impedance.

Fully headless operation, starts automatically at boot via systemd.

Uses Python with a virtual environment to manage dependencies.

Hardware

Raspberry Pi (tested on Pi 4)

INA219 current/voltage sensor (I2C)

AHT25 temperature/humidity sensor (I2C)

16x2 LCD with I2C backpack (PCF8574)

Python Script

import time
import board
import busio
from adafruit_ina219 import INA219
from adafruit_ahtx0 import AHTx0
from RPLCD.i2c import CharLCD

# Constants
PAGE_DELAY = 5
SHUNT_RESISTANCE = 0.1
VOLTAGE_HEALTHY = 11.5
VOLTAGE_MODERATE = 10.5
MAX_VOLTAGE = 12.6
MIN_VOLTAGE = 9.0

# Init I2C
i2c = busio.I2C(board.SCL, board.SDA)
ina219 = INA219(i2c)
aht25 = AHTx0(i2c)
lcd = CharLCD('PCF8574', 0x27, cols=16, rows=2)

def get_battery_status(voltage):
    if voltage >= VOLTAGE_HEALTHY:
        return "Healthy"
    elif voltage >= VOLTAGE_MODERATE:
        return "Moderate"
    else:
        return "Critical"

page = 0
while True:
    bus_v = ina219.bus_voltage
    current_a = ina219.current / 1000.0  # mA to A
    impedance = (bus_v / current_a) if current_a > 0.0001 else 0.0
    soc = max(0, min(100, (bus_v - MIN_VOLTAGE)/(MAX_VOLTAGE-MIN_VOLTAGE)*100))
    dod = 100 - soc
    temp = aht25.temperature
    hum = aht25.relative_humidity
    status = get_battery_status(bus_v)

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

Raspberry Pi Setup

Enable I2C

sudo raspi-config
# Interface Options -> I2C -> Enable

Update system

sudo apt update
sudo apt upgrade -y

Install dependencies

sudo apt install python3-pip python3-smbus i2c-tools python3-venv

Create working directory

mkdir -p ~/battery-monitor
cd ~/battery-monitor

Set up Python virtual environment

python3 -m venv batteryenv
source batteryenv/bin/activate

Install required Python libraries

pip install adafruit-circuitpython-ina219 adafruit-circuitpython-ahtx0 RPLCD

Create systemd service

sudo nano /etc/systemd/system/battery_monitor.service

Contents:

[Unit]
Description=Battery Monitoring System
After=multi-user.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/battery-monitor
Environment=PATH=/home/pi/battery-monitor/batteryenv/bin
ExecStart=/home/pi/battery-monitor/batteryenv/bin/python /home/pi/battery-monitor/battery_monitor.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target

Enable and start service

sudo systemctl daemon-reload
sudo systemctl enable battery_monitor.service
sudo systemctl start battery_monitor.service

Systemd Service Management

Action

Command

Check status

sudo systemctl status battery_monitor.service

View logs

journalctl -u battery_monitor.service -n 20 --no-pager

Stop service

sudo systemctl stop battery_monitor.service

Start service

sudo systemctl start battery_monitor.service

Restart service

sudo systemctl restart battery_monitor.service

Disable from boot

sudo systemctl disable battery_monitor.service

Notes

Ensure paths in the systemd file match your setup.

The script auto-starts on boot and runs headlessly.

If you move directories, update the service file accordingly.

Use journalctl to debug any startup issues.
