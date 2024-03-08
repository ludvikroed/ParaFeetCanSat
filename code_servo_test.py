import os
import busio
import digitalio
import board
import pwmio

import adafruit_rfm9x
import adafruit_dps310
import adafruit_gps
import adafruit_sdcard
import storage
from adafruit_motor import servo
from adafruit_lsm6ds.lsm6ds3 import LSM6DS3

import time
import json
import math

# sd card:
SD_CS = board.D10
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(SD_CS)
sdcard = adafruit_sdcard.SDCard(spi, cs)
vfs = storage.VfsFat(sdcard)
storage.mount(vfs, "/sd")

# Initialize I2C
i2c = board.I2C()  # uses board.SCL and board.SDA

# Initialize GPS module
gps = adafruit_gps.GPS_GtopI2C(i2c, debug=False)  # Use I2C interface
# Turn on everything in the GPS module
gps.send_command(b"PMTK314,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0")
# Set update rate to once a second (1hz)
gps.send_command(b"PMTK220,1000")

# Create DPS310 instance for barometric pressure and temperature
dps310 = adafruit_dps310.DPS310(i2c)

# Create LSM6DS3 instance for accelerometer and gyro sensor
sensor = LSM6DS3(i2c)

# Define radio parameters
RADIO_FREQ_MHZ = 915.0  # Frequency of the radio in Mhz. Must match your module! Can be a value like 915.0, 433.0, etc.
# Define pins connected to the RFM9x chip
CS = digitalio.DigitalInOut(board.RFM_CS)
RESET = digitalio.DigitalInOut(board.RFM_RST)
# Initialize RFM radio for transmitter
transmitter_rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)
transmitter_rfm9x.tx_power = 23  # Set transmit power
# Initialize RFM radio for receiver
receiver_rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)
receiver_rfm9x.tx_power = 23  # Set transmit power

#servo
# Set up PWM output for the servo
pwm = pwmio.PWMOut(board.D25, duty_cycle=2 ** 15, frequency=50)
my_servo = servo.Servo(pwm)

# Initialize flag and timer
send_reading = False

try:
    start_pressure = dps310.pressure
    start_pressure_error = False
except:
    start_pressure = 1000 #sett ca trykk på oppskytnignsdag
    start_pressure_error = True

last_sent_radio_data = time.monotonic()
data_list = {}
gps_data = {}
data_list_radio = {}
gps_data_to_send = {}
counter_radio = 0
counter_loop = 0
slipp_2_fallskjerm = 50
can_sat_in_air = False
drop_2_parachute = False
altitude = 0
time.sleep(1)  # Sleep for 1 second to allow sensors to initialize

print("-----------Starting loop----------")
while True:
    my_servo.angle = 0
    print("servo set to 0")
    time.sleep(5)
    my_servo.angle = 90
    print("servo set to 90")
    time.sleep(5)
